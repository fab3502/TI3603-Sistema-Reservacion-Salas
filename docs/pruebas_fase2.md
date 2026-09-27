# Pruebas internas — Fase 2 (Parte 5)

Suite: `python -m pytest` · 280 pruebas · Python 3.10+ · BD temporal por prueba.

| Cobertura mínima (14.1) | Requisito | Archivo de prueba |
|---|---|---|
| Flujo exitoso completo | RF-02 a RF-09, RF-13, RF-15, RF-17 | integration/test_flujos_app_service.py::test_flujo_exitoso_completo |
| Carné duplicado con otra capitalización | RF-02 | unit/test_database.py · integration/test_flujos_app_service.py |
| Campos vacíos y espacios periféricos | RF-02, RNF-05 | unit/test_validaciones.py · integration/…::TestEstudiantes |
| Tipos y formatos inválidos | RNF-05 | unit/test_validaciones.py |
| Fechas pasadas, inexistentes, hoy con hora pasada | RN-02, RN-03 | unit/test_validaciones.py::TestFecha, TestReservaHoy |
| Horario fuera de rango y duración inválida | RN-04, RN-05, RN-06 | unit/test_validaciones.py::TestHoraYHorario, TestNumericos |
| Conflicto total, parcial, envolvente, consecutivo | RN-09, RN-10 | unit/test_reglas_negocio.py::TestSuperposicion |
| Capacidad exacta, excedida, cero, decimal | RN-07 | unit/test_validaciones.py::TestNumericos |
| Estudiante inexistente o inactivo | RN-01 | unit/test_reglas_negocio.py |
| Sala inexistente o fuera de servicio | RN-08 | unit/test_reglas_negocio.py |
| Máximo de tres reservaciones activas | RN-11 | unit/test_reglas_negocio.py::TestLimiteReservas |
| Cancelación exitosa, inexistente y repetida | RF-09, RN-12 | integration/…::TestModificacionCancelacion |
| Persistencia, reinicio y continuidad de IDs | RF-01, RN-13 | unit/test_database.py · integration/…::TestPersistenciaYRecuperacion |
| Recuperación después de errores | RNF-05, RNF-06 | integration/…::test_recuperacion_despues_de_errores |
| Carga mínima de rendimiento | RNF-09 | integration/test_rendimiento.py |
| Creación y modificación de salas | RF-12 | integration/…::TestSalas |
| Cambio de estado de estudiantes y salas | RF-11, RF-12 | integration/…::TestEstudiantes, TestSalas |
| Modificación válida e inválida de reservaciones | RF-13 | integration/…::TestModificacionCancelacion |
| Series recurrentes con y sin conflictos | RF-14 | integration/…::TestRecurrencia |
| Cancelación de una ocurrencia y de una serie | RF-14 | integration/…::TestRecurrencia |
| Combinación de filtros en el panel | RF-15 | unit/test_panel_historial.py · integration/test_gui_panel_reportes.py |
| Exportación CSV y cancelación del selector | RF-16 | integration/test_gui_panel_reportes.py |
| Actualización del panel después de una operación | RF-15 | unit/test_panel_historial.py · integration/test_gui_panel_reportes.py |
| Persistencia e integridad en SQLite | RNF-06, RNF-08 | unit/test_database.py::TestIntegridad |
| Registro y consulta de auditoría | RF-17 | unit/test_panel_historial.py::TestHistorial |

Técnicas aplicadas: partición de equivalencia y valores límite (test_validaciones), tabla de decisión (TestTablaDecisionCrearReservacion), escenarios (test_flujos_app_service) y automatización unitaria e integración. La suite completa sirve como regresión en las fases 6 y 7.
