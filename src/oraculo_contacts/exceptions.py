"""Jerarquía de errores controlados de la aplicación."""


class OraculoError(Exception):
    """Error esperado que puede comunicarse sin traza al usuario."""


class ImportError(OraculoError):
    """El origen no pudo importarse de forma segura."""


class ReportError(OraculoError):
    """El reporte no pudo generarse o escribirse."""
