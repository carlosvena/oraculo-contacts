"""Interfaz visual local, en español y estrictamente de solo lectura."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import streamlit as st

from oraculo_contacts.application.review_workflow import DecisionHistory, preview_contacts
from oraculo_contacts.domain.changeset import ChangeDecision, build_changeset
from oraculo_contacts.domain.models import Contact
from oraculo_contacts.domain.quality_analyzer import analyze_quality
from oraculo_contacts.domain.recommendations import RecommendationEngine
from oraculo_contacts.exceptions import OraculoError
from oraculo_contacts.infrastructure.contact_import_service import import_contacts
from oraculo_contacts.infrastructure.diagnostic_report import (
    diagnostic_payload,
    render_diagnostic_html,
    render_diagnostic_json,
)
from oraculo_contacts.infrastructure.import_models import ImportResult
from oraculo_contacts.infrastructure.safe_export import export_copy
from oraculo_contacts.infrastructure.workspace import save_workspace, source_checksum
from oraculo_contacts.ui.view_models import (
    PresenceFilter,
    QualityLevel,
    contact_summary,
    dashboard_metrics,
    filter_contacts,
    mask_email,
    mask_phone,
)

st.set_page_config(page_title="ORÁCULO CONTACTS", page_icon="🔮", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px;}
    [data-testid="stMetric"] {background:#f7f8fa; border:1px solid #e5e7eb; padding:1rem;
      border-radius:12px; box-shadow:0 1px 2px rgba(0,0,0,.03);}
    .safe-banner {background:#edf8f2; color:#17653a; border:1px solid #b9e4ca;
      border-radius:10px; padding:.7rem 1rem; font-weight:650; margin:.5rem 0 1.25rem;}
    .warning-banner {background:#fff8e8; color:#805b00; border:1px solid #f3d483;
      border-radius:10px; padding:.7rem 1rem; font-weight:650; margin:.5rem 0 1rem;}
    .muted-card {background:#f8fafc; border-left:4px solid #64748b; padding:.7rem 1rem;
      border-radius:8px; margin:.35rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


class _ButtonColumn(Protocol):
    """Superficie mínima de una columna Streamlit usada para decisiones."""

    def button(self, label: str, *, key: str) -> bool:
        """Renderizar un botón y devolver si fue activado."""
        ...


def _load_contacts() -> tuple[Contact, ...] | None:
    """Asistir una importación segura y mantenerla únicamente en sesión."""
    if "active_contacts" in st.session_state:
        result: ImportResult = st.session_state.import_result
        st.sidebar.success(f"Sesión activa: {len(result.contacts)} contactos")
        return result.contacts
    st.subheader("Abrí tus contactos")
    st.write(
        "Para exportar tus contactos desde Google: "
        "Google Contacts → Exportar → CSV de Google o vCard."
    )
    buttons = st.columns(3)
    if buttons[0].button(
        "Probar con datos de demostración", type="primary", use_container_width=True
    ):
        demo_path = Path(__file__).with_name("demo_contacts.json")
        content = demo_path.read_text(encoding="utf-8")
        result = import_contacts(demo_path.name, content)
        _activate_import(result, content.encode("utf-8"), demo_path.name)
        st.rerun()
    if buttons[1].button("Importar Google Contacts CSV", use_container_width=True):
        st.session_state.import_mode = "csv"
    if buttons[2].button("Importar archivo VCF", use_container_width=True):
        st.session_state.import_mode = "vcf"
    mode = st.session_state.get("import_mode")
    st.markdown(
        '<div class="safe-banner">ORÁCULO trabajará en modo solo lectura. '
        "El archivo original no será modificado.</div>",
        unsafe_allow_html=True,
    )
    if mode is None:
        st.caption("También se admiten archivos JSON desde la pantalla de importación.")
        return None
    types = ("csv",) if mode == "csv" else ("vcf", "vcard", "json")
    uploaded = st.file_uploader("Seleccionar archivo", type=types)
    if uploaded is None:
        if st.button("Cancelar importación"):
            st.session_state.pop("import_mode", None)
            st.rerun()
        return None
    try:
        raw = uploaded.getvalue()
        content = raw.decode("utf-8-sig")
        result = import_contacts(uploaded.name, content)
        st.write(
            f"**Archivo:** {uploaded.name} · **Tamaño:** {len(raw):,} bytes · "
            f"**Formato:** {result.format.value.upper()}"
        )
        summary = st.columns(4)
        summary[0].metric("Contactos válidos", len(result.contacts))
        summary[1].metric("Con advertencias", result.contacts_with_warnings)
        summary[2].metric("Filas rechazadas", result.rejected_rows)
        summary[3].metric("Campos desconocidos", len(result.unknown_fields))
        st.write("**Campos reconocidos:**", ", ".join(result.recognized_fields) or "Ninguno")
        if result.unknown_fields:
            st.write("**Campos desconocidos:**", ", ".join(result.unknown_fields))
        st.caption("Vista previa segura de hasta 10 contactos")
        st.dataframe(
            [contact_summary(contact, 0) for contact in result.contacts[:10]],
            hide_index=True,
            width="stretch",
        )
        actions = st.columns(2)
        if actions[0].button("Analizar en modo seguro", type="primary", use_container_width=True):
            _activate_import(result, raw, uploaded.name)
            st.rerun()
        if actions[1].button("Cancelar sin guardar", use_container_width=True):
            st.session_state.pop("import_mode", None)
            st.rerun()
    except UnicodeDecodeError:
        st.error("El archivo debe estar codificado como UTF-8.")
    except OraculoError as error:
        st.error(f"No pudimos cargar el archivo: {error}")
    return None


def _activate_import(result: ImportResult, raw: bytes, filename: str) -> None:
    """Activar una instantánea en memoria después de confirmación humana."""
    st.session_state.active_contacts = result.contacts
    st.session_state.import_result = result
    st.session_state.source_checksum = source_checksum(raw)
    st.session_state.source_filename = filename
    st.session_state.review_history = DecisionHistory((), build_changeset(result.contacts))
    st.session_state.pop("import_mode", None)


def _dashboard(contacts: tuple[Contact, ...]) -> None:
    """Mostrar una síntesis ejecutiva de la colección."""
    st.header("Resumen")
    metrics = dashboard_metrics(contacts)
    first = st.columns(6)
    cards = (
        ("Contactos", metrics.contacts),
        ("Favoritos", metrics.favorites),
        ("Cumpleaños", metrics.birthdays),
        ("Con notas", metrics.with_notes),
        ("Teléfonos", metrics.phones),
        ("Correos", metrics.emails),
    )
    for column, (label, value) in zip(first, cards, strict=True):
        column.metric(label, value)
    second = st.columns(5)
    cards_2 = (
        ("Direcciones", metrics.addresses),
        ("Calidad general", f"{metrics.quality_score}/100"),
        ("Posibles duplicados", metrics.duplicate_candidates),
        ("Inconsistencias", metrics.inconsistencies),
        ("Oportunidades", metrics.opportunities),
    )
    for column, (label, value) in zip(second, cards_2, strict=True):
        column.metric(label, value)
    st.caption("Las métricas se calculan localmente. Ningún contacto fue modificado.")
    result: ImportResult = st.session_state.import_result
    imported = st.columns(3)
    imported[0].metric(
        "Organizaciones", len({item.organization for item in contacts if item.organization})
    )
    imported[1].metric("Contactos sin nombre", sum(not item.display_name for item in contacts))
    imported[2].metric("Advertencias de importación", len(result.warnings))


def _contacts(contacts: tuple[Contact, ...]) -> None:
    """Explorar, filtrar y abrir una ficha individual."""
    st.header("Contactos")
    quality_report = analyze_quality(contacts)
    scores = {item.contact_ref: item.score for item in quality_report.contacts}
    assessments = {item.contact_ref: item for item in quality_report.contacts}
    query = st.text_input(
        "Búsqueda rápida",
        placeholder="Nombre, organización, teléfono o correo (búsqueda local)",
    )
    filters = st.columns(6)
    favorite = PresenceFilter(filters[0].selectbox("Favorito", list(PresenceFilter)))
    birthday = PresenceFilter(filters[1].selectbox("Cumpleaños", list(PresenceFilter)))
    phone = PresenceFilter(filters[2].selectbox("Teléfono", list(PresenceFilter)))
    email = PresenceFilter(filters[3].selectbox("Correo", list(PresenceFilter)))
    level = QualityLevel(filters[4].selectbox("Calidad", list(QualityLevel)))
    address = PresenceFilter(filters[5].selectbox("Dirección", list(PresenceFilter)))
    organizations = ("", *sorted({item.organization for item in contacts if item.organization}))
    labels = ("", *sorted({label for item in contacts for label in item.labels}))
    extra_filters = st.columns(2)
    organization = extra_filters[0].selectbox(
        "Organización", organizations, format_func=lambda value: value or "Todas"
    )
    label = extra_filters[1].selectbox(
        "Etiqueta", labels, format_func=lambda value: value or "Todas"
    )
    visible = filter_contacts(
        contacts,
        query=query,
        favorite=favorite,
        birthday=birthday,
        phone=phone,
        email=email,
        address=address,
        quality=level,
        organization=organization,
        label=label,
    )
    st.caption(f"{len(visible)} contacto(s). Teléfonos y correos aparecen ocultos en esta vista.")
    st.dataframe(
        [contact_summary(contact, scores[contact.source_id]) for contact in visible],
        hide_index=True,
        width="stretch",
        column_config={"Calidad": st.column_config.ProgressColumn(min_value=0, max_value=100)},
    )
    if not visible:
        return
    selected_ref = st.selectbox(
        "Abrir ficha individual",
        [contact.source_id for contact in visible],
        format_func=lambda ref: next(
            (contact.display_name or "Sin nombre")
            for contact in visible
            if contact.source_id == ref
        ),
    )
    selected = next(contact for contact in visible if contact.source_id == selected_ref)
    assessment = assessments[selected_ref]
    st.subheader(selected.display_name or "Contacto sin nombre")
    left, right = st.columns((2, 1))
    with left:
        st.write("**Correos:**", ", ".join(selected.emails) or "Sin correo")
        st.write("**Teléfonos:**", ", ".join(selected.phones) or "Sin teléfono")
        st.write("**Direcciones:**", ", ".join(selected.addresses) or "Sin dirección")
        st.write("**Organización:**", selected.organization or "Sin organización")
        st.write("**Cargo:**", selected.job_title or "Sin cargo")
        st.write("**Etiquetas:**", ", ".join(selected.labels) or "Sin etiquetas")
        st.write(
            "**Cumpleaños:**", selected.birthday.isoformat() if selected.birthday else "Sin dato"
        )
        st.write("**Favorito:**", "Sí" if selected.favorite else "No")
        with st.expander("Mostrar notas protegidas"):
            st.write(selected.notes or "Sin notas")
    with right:
        st.metric("Score de calidad", f"{assessment.score}/100")
        missing = []
        if not (selected.display_name or selected.given_name or selected.family_name):
            missing.append("Nombre")
        if not selected.emails:
            missing.append("Correo")
        if not selected.phones:
            missing.append("Teléfono")
        if not selected.birthday:
            missing.append("Cumpleaños")
        st.write("**Campos faltantes:**", ", ".join(missing) or "Ninguno")
        st.write("**Inconsistencias:**")
        if assessment.issues:
            for issue in assessment.issues:
                st.write(f"- {issue.reason}")
                st.caption(f"Recomendación: {issue.recommendation}")
        else:
            st.write("No se detectaron inconsistencias.")


def _duplicates(contacts: tuple[Contact, ...]) -> None:
    """Comparar candidatos lado a lado sin permitir fusiones."""
    st.header("Posibles duplicados")
    st.markdown(
        '<div class="warning-banner">⚠ ORÁCULO no fusiona automáticamente</div>',
        unsafe_allow_html=True,
    )
    candidates = analyze_quality(contacts).duplicate_candidates
    if not candidates:
        st.success("No se detectaron candidatos con las reglas actuales.")
        return
    by_ref = {contact.source_id: contact for contact in contacts}
    for index, candidate in enumerate(candidates, 1):
        with st.expander(
            f"Candidato {index} · confianza {candidate.confidence:.0%} · "
            f"riesgo {candidate.severity.value}",
            expanded=index == 1,
        ):
            st.write("**Motivos:** " + " ".join(candidate.reasons))
            st.write("**Campos coincidentes:** " + ", ".join(candidate.matched_on))
            columns = st.columns(2)
            for column, reference in zip(columns, candidate.contact_refs, strict=True):
                contact = by_ref[reference]
                with column:
                    st.subheader(contact.display_name or "Sin nombre")
                    st.write("Referencia:", reference)
                    st.write("Correo:", mask_email(contact.emails[0]) if contact.emails else "—")
                    st.write("Teléfono:", mask_phone(contact.phones[0]) if contact.phones else "—")
            st.caption(candidate.recommendation)


def _plan(contacts: tuple[Contact, ...]) -> None:
    """Mostrar recomendaciones y registrar intenciones solo en la sesión."""
    st.header("Plan de mejora")
    plan = RecommendationEngine().build_plan(contacts)
    summary = st.columns(4)
    summary[0].metric("Recomendaciones", len(plan.recommendations))
    summary[1].metric("Tiempo estimado", f"{plan.estimated_minutes} min")
    summary[2].metric("Riesgo general", plan.overall_risk.value)
    summary[3].metric("Contactos", plan.contacts_analyzed)
    st.caption(plan.explanation)
    decisions = st.session_state.setdefault("recommendation_decisions", {})
    for index, recommendation in enumerate(plan.recommendations, 1):
        with st.container(border=True):
            top = st.columns((4, 1))
            top[0].subheader(f"{index}. {recommendation.title}")
            top[1].metric("Prioridad", f"{recommendation.priority_score:.1f}")
            details = st.columns(4)
            details[0].write(f"**Beneficio:** {recommendation.benefit}/100")
            details[1].write(f"**Confianza:** {recommendation.confidence:.0%}")
            details[2].write(f"**Riesgo:** {recommendation.risk.value}")
            details[3].write(f"**Esfuerzo:** {recommendation.effort.value}")
            st.write(recommendation.explanation)
            st.caption("Contactos: " + ", ".join(recommendation.contact_refs))
            choices = ("Sin decidir", "Revisar después", "Descartada", "Aceptada como intención")
            current = decisions.get(recommendation.recommendation_id, "Sin decidir")
            decision = st.selectbox(
                "Estado en esta sesión",
                choices,
                index=choices.index(current),
                key=f"decision-{recommendation.recommendation_id}",
            )
            decisions[recommendation.recommendation_id] = decision
    st.info("Estas selecciones viven solo en memoria y se pierden al cerrar la sesión.")


def _reports(contacts: tuple[Contact, ...]) -> None:
    """Ofrecer informes explícitos enmascarados por defecto."""
    st.header("Informe de diagnóstico")
    include_sensitive = st.checkbox("Incluir datos sensibles en el informe", value=False)
    if include_sensitive:
        st.warning(
            "El informe incluirá notas, teléfonos, correos y direcciones completos. "
            "Guardalo únicamente en una ubicación privada."
        )
    result: ImportResult = st.session_state.import_result
    payload = diagnostic_payload(contacts, result.warnings, include_sensitive=include_sensitive)
    json_report = render_diagnostic_json(payload)
    html_report = render_diagnostic_html(payload)
    downloads = st.columns(2)
    downloads[0].download_button(
        "Descargar informe JSON",
        json_report,
        file_name="oraculo-diagnostico.json",
        mime="application/json",
        use_container_width=True,
    )
    downloads[1].download_button(
        "Descargar informe HTML",
        html_report,
        file_name="oraculo-diagnostico.html",
        mime="text/html",
        use_container_width=True,
    )
    st.caption("La descarga no modifica el archivo original ni los contactos.")


def _review_changes(contacts: tuple[Contact, ...]) -> None:
    """Revisar propuestas una por una sin tocar contactos."""
    st.header("Revisión de cambios")
    st.info("¿Qué está haciendo ORÁCULO? Te muestra opciones; solo vos decidís.")
    history: DecisionHistory = st.session_state.review_history
    actions = st.columns(5)
    if actions[0].button("Aprobar cambios de bajo riesgo"):
        st.session_state.review_history = history.record(history.current.approve_low_risk())
        st.rerun()
    if actions[1].button("Deshacer", disabled=not history.past):
        st.session_state.review_history = history.undo()
        st.rerun()
    if actions[2].button("Rehacer", disabled=not history.future):
        st.session_state.review_history = history.redo()
        st.rerun()
    selected: set[str] = st.session_state.setdefault("selected_changes", set())
    if actions[3].button("Rechazar seleccionadas", disabled=not selected):
        updated = history.current
        for change_id in selected:
            updated = updated.decide(change_id, ChangeDecision.REJECTED)
        st.session_state.review_history = history.record(updated)
        st.session_state.selected_changes = set()
        st.rerun()
    if actions[4].button("Restaurar decisiones"):
        st.session_state.review_history = history.record(history.current.restore())
        st.rerun()
    changeset = history.current
    summary = changeset.summary()
    metrics = st.columns(5)
    for column, (label, value) in zip(
        metrics,
        (
            ("Propuestas", summary.total),
            ("Aprobadas", summary.approved),
            ("Rechazadas", summary.rejected),
            ("Pospuestas", summary.postponed),
            ("Bloqueadas", summary.blocked),
        ),
        strict=True,
    ):
        column.metric(label, value)
    if not changeset.changes:
        st.success("No hay cambios sugeridos para revisar.")
        return
    by_ref = {contact.source_id: contact for contact in contacts}
    for category in dict.fromkeys(change.category for change in changeset.changes):
        st.subheader(category.capitalize())
        for change in (item for item in changeset.changes if item.category == category):
            contact = by_ref.get(change.contact_ref)
            label = contact.display_name if contact else change.contact_ref
            with st.expander(f"{label or 'Sin nombre'} · {change.field} · {change.decision.value}"):
                checked = st.checkbox(
                    "Seleccionar para acción masiva",
                    value=change.change_id in selected,
                    key=f"select-{change.change_id}",
                )
                if checked:
                    selected.add(change.change_id)
                else:
                    selected.discard(change.change_id)
                if change.protected:
                    st.warning("Campo protegido: requiere aprobación individual explícita.")
                left, right = st.columns(2)
                left.write("**Antes**")
                left.code(_safe_change_value(change.field, change.before))
                right.write("**Sugerido**")
                right.code(_safe_change_value(change.field, change.after))
                st.write(change.reason)
                st.caption(
                    f"Evidencia: {' '.join(change.evidence)} · Confianza {change.confidence:.0%} · "
                    f"Riesgo {change.risk.value} · Regla {change.rule_version} · "
                    f"Impacto {change.estimated_impact}/100"
                )
                decisions = st.columns(4)
                _decision_button(
                    decisions[0],
                    "Aprobar",
                    change.change_id,
                    ChangeDecision.APPROVED,
                    change.protected,
                )
                _decision_button(
                    decisions[1], "Rechazar", change.change_id, ChangeDecision.REJECTED
                )
                _decision_button(
                    decisions[2], "Posponer", change.change_id, ChangeDecision.POSTPONED
                )
                _decision_button(
                    decisions[3], "Restaurar", change.change_id, ChangeDecision.PENDING
                )


def _decision_button(
    column: _ButtonColumn,
    label: str,
    change_id: str,
    decision: ChangeDecision,
    protected: bool = False,
) -> None:
    if column.button(label, key=f"{label}-{change_id}"):
        history: DecisionHistory = st.session_state.review_history
        updated = history.current.decide(
            change_id,
            decision,
            individual_protected=protected and decision is ChangeDecision.APPROVED,
        )
        st.session_state.review_history = history.record(updated)
        st.rerun()


def _safe_change_value(field: str, value: str) -> str:
    if field == "email":
        return mask_email(value)
    if field == "phone":
        return mask_phone(value)
    return value


def _preview_result(contacts: tuple[Contact, ...]) -> None:
    """Comparar agenda original y propuesta sin exponer tablas sensibles."""
    st.header("Vista previa del resultado")
    changeset = st.session_state.review_history.current
    proposed = preview_contacts(contacts, changeset)
    before_score = analyze_quality(contacts).quality_score
    after_score = analyze_quality(proposed).quality_score
    summary = changeset.summary()
    metrics = st.columns(6)
    values = (
        ("Cambios", summary.total),
        ("Aprobados", summary.approved),
        ("Rechazados", summary.rejected),
        ("Pospuestos", summary.postponed),
        ("Conflictos", summary.conflicts),
        ("Calidad", f"{before_score} → {after_score}"),
    )
    for column, (label, value) in zip(metrics, values, strict=True):
        column.metric(label, value)
    filter_ = st.selectbox(
        "Filtrar vista",
        (
            "Solo modificados",
            "Solo conflictos",
            "Solo alto riesgo",
            "Solo campos protegidos",
            "Solo duplicados",
            "Solo teléfonos",
            "Solo nombres",
            "Solo correos",
            "Todos",
        ),
    )
    approved_refs = {
        item.contact_ref for item in changeset.changes if item.decision is ChangeDecision.APPROVED
    }
    rows = []
    for before, after in zip(contacts, proposed, strict=True):
        contact_changes = [
            item for item in changeset.changes if item.contact_ref == before.source_id
        ]
        if filter_ == "Solo modificados" and before.source_id not in approved_refs:
            continue
        if filter_ == "Solo conflictos" and not any(
            item.decision is ChangeDecision.CONFLICT for item in contact_changes
        ):
            continue
        if filter_ == "Solo alto riesgo" and not any(
            item.risk.value == "high" for item in contact_changes
        ):
            continue
        if filter_ == "Solo campos protegidos" and not any(
            item.protected for item in contact_changes
        ):
            continue
        category_filters = {
            "Solo duplicados": "duplicados potenciales",
            "Solo teléfonos": "teléfonos",
            "Solo nombres": "nombres",
            "Solo correos": "correos",
        }
        if filter_ in category_filters and not any(
            item.category == category_filters[filter_] for item in contact_changes
        ):
            continue
        rows.append(
            {
                "Contacto": before.display_name or "Sin nombre",
                "ANTES": before.display_name,
                "DESPUÉS": after.display_name,
                "Modificado": before != after,
            }
        )
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(
        "Teléfonos, correos y campos protegidos no se muestran completos en esta tabla general."
    )


def _export_reviewed(contacts: tuple[Contact, ...]) -> None:
    """Exportar una copia nueva solo después de confirmación."""
    st.header("Exportar copia mejorada")
    st.info("¿Qué está haciendo ORÁCULO? Creará archivos nuevos. El original permanecerá intacto.")
    folder = st.text_input("Carpeta donde guardar la copia")
    format_ = st.selectbox("Formato", ("csv", "vcf", "json"))
    confirm = st.checkbox("Confirmo que deseo crear una copia nueva")
    if st.button("Exportar copia mejorada", type="primary", disabled=not (folder and confirm)):
        try:
            result: ImportResult = st.session_state.import_result
            exported = export_copy(
                contacts,
                st.session_state.review_history.current,
                Path(folder),
                format_=format_,
                source_filename=st.session_state.source_filename,
                source_checksum=st.session_state.source_checksum,
                warnings=tuple(item.message for item in result.warnings),
            )
            st.session_state.last_export = exported
            st.success("Trabajo completado")
            summary = st.session_state.review_history.current.summary()
            st.write(
                f"Contactos analizados: {len(contacts)} · Cambios aplicados: {summary.approved}"
            )
            st.write(f"Copia: {exported.output} · Manifiesto: {exported.manifest}")
            st.success("Garantía: el archivo original permanece intacto.")
        except OraculoError as error:
            st.error(str(error))


def _workspace_controls(contacts: tuple[Contact, ...]) -> None:
    """Mostrar persistencia local solo cuando el usuario la activa."""
    with st.sidebar.expander("Sesión local opcional"):
        enabled = st.checkbox("Guardar sesión local", value=False)
        if enabled:
            st.warning("Se guardarán contactos y checksum. Las notas se omitirán.")
            destination = st.text_input("Carpeta local elegida por vos")
            consent = st.checkbox("Confirmo que deseo guardar esta copia local")
            if st.button("Guardar sesión", disabled=not (destination and consent)):
                try:
                    output = save_workspace(
                        contacts,
                        Path(destination),
                        source_sha256=st.session_state.source_checksum,
                        repository_root=Path(__file__).parents[3],
                    )
                    st.success(f"Sesión guardada en {output}")
                except OraculoError as error:
                    st.error(str(error))
    if st.sidebar.button("Cerrar sesión y borrar datos temporales", type="secondary"):
        for key in tuple(st.session_state):
            del st.session_state[key]
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()


def main() -> None:
    """Componer la navegación principal."""
    st.title("ORÁCULO CONTACTS")
    st.markdown(
        '<div class="safe-banner">🛡 Modo seguro: solo lectura</div>', unsafe_allow_html=True
    )
    contacts = _load_contacts()
    if contacts is None:
        return
    _workspace_controls(contacts)
    st.sidebar.divider()
    st.sidebar.progress(
        0.4, text="1 Importar ✓ · 2 Analizar ✓ · 3 Revisar · 4 Vista previa · 5 Exportar"
    )
    page = st.sidebar.radio(
        "Navegación",
        (
            "Resumen",
            "Contactos",
            "Posibles duplicados",
            "Plan de mejora",
            "Revisión de cambios",
            "Vista previa del resultado",
            "Exportar copia",
            "Informes",
        ),
    )
    {
        "Resumen": _dashboard,
        "Contactos": _contacts,
        "Posibles duplicados": _duplicates,
        "Plan de mejora": _plan,
        "Revisión de cambios": _review_changes,
        "Vista previa del resultado": _preview_result,
        "Exportar copia": _export_reviewed,
        "Informes": _reports,
    }[page](contacts)


main()
