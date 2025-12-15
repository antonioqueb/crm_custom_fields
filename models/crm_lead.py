# models/crm_lead.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    def _get_or_create_service_uom(self):
        """
        Odoo 19: uom.uom y sus campos pueden variar (por ejemplo category_id).
        Estrategia robusta:
        - Buscar "Unidad de servicio" (case-insensitive).
        - Si no existe, crearla copiando campos compatibles desde la UdM base
          uom.product_uom_unit ("Unidades"), sin asumir campos fijos.
        - Fallback final: uom.product_uom_unit.
        """
        UoM = self.env['uom.uom'].sudo()
        unit = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

        # 1) Buscar existente
        service_uom = UoM.search([('name', '=ilike', 'Unidad de servicio')], limit=1)
        if not service_uom:
            service_uom = UoM.search([('name', 'ilike', 'Unidad de servicio')], limit=1)
        if service_uom:
            return service_uom

        # 2) Crear por copia de "Unidades" (si existe)
        if not unit:
            return False

        vals = {'name': 'Unidad de servicio'}

        # Copiar solo campos que existan en tu versión
        candidates = [
            'category_id',
            'uom_type',
            'factor',
            'factor_inv',
            'ratio',
            'ratio_inv',
            'rounding',
            'active',
            'relative_uom_id',
        ]
        for f in candidates:
            if f in unit._fields:
                vals[f] = unit[f]

        # Asegurar activo si existe
        if 'active' in UoM._fields:
            vals['active'] = True

        try:
            return UoM.create(vals)
        except Exception:
            _logger.exception("Error creando UdM 'Unidad de servicio'. vals=%s", vals)
            return unit

    # -------------------------------------------------------------------------
    # INFORMACIÓN BÁSICA DEL PROSPECTO
    # -------------------------------------------------------------------------
    company_size = fields.Selection([
        ('micro', 'Micro'),
        ('pequena', 'Pequeña'),
        ('mediana', 'Mediana'),
        ('grande', 'Grande')
    ], string="Tamaño de Empresa")

    industrial_sector = fields.Char(string="Giro Industrial/Actividad Económica")

    # ORIGEN Y CLASIFICACIÓN COMERCIAL
    prospect_priority = fields.Selection([
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('estrategico', 'Estratégico')
    ], string="Prioridad del Prospecto", default='media')

    estimated_business_potential = fields.Float(string="Potencial Estimado de Negocio")

    # INFORMACIÓN OPERATIVA
    access_restrictions = fields.Text(string="Restricciones de Acceso")
    allowed_collection_schedules = fields.Text(string="Horarios Permitidos para Recolección")
    current_container_types = fields.Text(string="Tipo de Contenedores Actuales")
    special_handling_conditions = fields.Text(string="Condiciones Especiales de Manejo")
    seasonality = fields.Text(string="Estacionalidad")

    # INFORMACIÓN REGULATORIA
    waste_generator_registration = fields.Char(string="Registro como Generador de Residuos")
    environmental_authorizations = fields.Text(string="Autorizaciones Ambientales Vigentes")
    quality_certifications = fields.Text(string="Certificaciones de Calidad")
    other_relevant_permits = fields.Text(string="Otros Permisos Relevantes")

    # COMPETENCIA Y MERCADO
    current_service_provider = fields.Char(string="Proveedor Actual de Servicios")
    current_costs = fields.Float(string="Costos Actuales")
    current_provider_satisfaction = fields.Selection([
        ('muy_bajo', 'Muy Bajo'),
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('muy_alto', 'Muy Alto')
    ], string="Nivel de Satisfacción con Proveedor Actual")

    reason_for_new_provider = fields.Text(string="Motivo de Búsqueda de Nuevo Proveedor")

    # REQUERIMIENTOS ESPECIALES
    specific_certificates_needed = fields.Text(string="Necesidad de Certificados Específicos")
    reporting_requirements = fields.Text(string="Requerimientos de Reporteo")
    service_urgency = fields.Selection([
        ('inmediata', 'Inmediata'),
        ('1_semana', '1 Semana'),
        ('1_mes', '1 Mes'),
        ('3_meses', '3 Meses'),
        ('sin_prisa', 'Sin Prisa')
    ], string="Urgencia del Servicio")

    estimated_budget = fields.Float(string="Presupuesto Estimado")

    # CAMPOS DE SEGUIMIENTO
    next_contact_date = fields.Datetime(string="Fecha de Próximo Contacto")
    pending_actions = fields.Text(string="Acciones Pendientes")
    conversation_notes = fields.Text(string="Notas de Conversaciones")

    # Campos de información del servicio
    service_frequency = fields.Selection([
        ('diaria', 'Diaria'),
        ('2_veces_semana', '2 veces por semana'),
        ('3_veces_semana', '3 veces por semana'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('bimensual', 'Bimensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('bajo_demanda', 'Bajo demanda'),
        ('emergencia', 'Emergencia/Urgente'),
        ('una_sola_vez', 'Una sola vez'),
        ('estacional', 'Estacional'),
        ('irregular', 'Irregular')
    ], string="Frecuencia del Servicio")

    pickup_location_id = fields.Many2one(
        'res.partner',
        string="Ubicación de recolección",
        help="Seleccione una dirección de recolección asociada al cliente.",
        ondelete='set null'
    )


    residue_line_ids = fields.One2many('crm.lead.residue', 'lead_id', string="Listado de Residuos")

    residue_new = fields.Boolean(string="¿Residuo Nuevo?")
    show_sample_alert = fields.Boolean(string="Mostrar alerta de muestra", compute="_compute_show_sample_alert", store=True)
    sample_result_file = fields.Binary(string="Archivo de Resultados de Muestra")
    sample_result_filename = fields.Char(string="Nombre del Archivo de Resultados de Muestra")

    requiere_visita = fields.Boolean(string="Requiere visita presencial")
    show_visita_alert = fields.Boolean(string="Mostrar alerta visita", compute="_compute_show_visita_alert", store=True)
    visita_validation_file = fields.Binary(string="Archivo de validación de visita")
    visita_validation_filename = fields.Char(string="Nombre del archivo de validación de visita")

    @api.depends('residue_new', 'sample_result_file')
    def _compute_show_sample_alert(self):
        for record in self:
            record.show_sample_alert = record.residue_new and not bool(record.sample_result_file)

    @api.depends('requiere_visita', 'visita_validation_file')
    def _compute_show_visita_alert(self):
        for record in self:
            record.show_visita_alert = record.requiere_visita and not bool(record.visita_validation_file)

    def _create_service_from_residue(self, residue):
        """
        Crear un producto de tipo servicio desde un residuo.
        Requerimientos:
        - NO default_code (referencia interna)
        - NO description_sale (sin resumen en cotización)
        - UdM = "Unidad de servicio"
        Nota Odoo 19:
        - product.product NO tiene uom_po_id (de ahí tu error). Solo usamos uom_id.
        """
        self.ensure_one()

        service_name = (residue.name or '').strip()
        if not service_name:
            raise ValidationError("No se puede crear el servicio: el nombre del residuo está vacío.")

        Category = self.env['product.category'].sudo()
        Product = self.env['product.product'].sudo()

        category = Category.search([('name', 'ilike', 'servicios de residuos')], limit=1)
        if not category:
            category = Category.create({'name': 'Servicios de Residuos'})

        service_uom = self._get_or_create_service_uom() or self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

        vals = {
            'name': service_name,
            'type': 'service',
            'categ_id': category.id,
            'sale_ok': True,
            'purchase_ok': False,

            # Sin resumen en cotización
            'description_sale': '',

            # UdM (product.product sí tiene uom_id en tu instancia)
            'uom_id': service_uom.id if service_uom else False,

            # Sin referencia interna
            # 'default_code': ...
            # 'code': ...
        }

        # Escribir solo campos que existan (blindaje extra)
        safe_vals = {k: v for k, v in vals.items() if k in Product._fields}

        try:
            return Product.create(safe_vals)
        except Exception as e:
            _logger.exception("Error creando servicio desde CRM. vals=%s", safe_vals)
            raise ValidationError(
                f"No se pudo crear el servicio automáticamente. Detalle técnico: {str(e)}"
            )


class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    def _default_service_uom(self):
        lead = self.env['crm.lead']
        uom = lead._get_or_create_service_uom()
        return uom or self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

    lead_id = fields.Many2one('crm.lead', string="Lead/Oportunidad", required=True, ondelete='cascade')

    # -------------------------------------------------------------------------
    # LÓGICA DE SERVICIO / RESIDUO
    # -------------------------------------------------------------------------
    create_new_service = fields.Boolean(
        string="¿Nuevo Servicio?",
        default=False,
        help="Marca si es un servicio NUEVO. Desmarca para seleccionar uno existente."
    )

    existing_service_id = fields.Many2one(
        'product.product',
        string="Servicio Existente",
        domain=[('sale_ok', '=', True), ('type', '=', 'service')],
        help="Selecciona un servicio existente del catálogo"
    )

    name = fields.Char(
        string="Nombre del Residuo",
        required=False,
        help="Nombre descriptivo para crear un nuevo servicio"
    )

    residue_type = fields.Selection(
        selection=[('rsu', 'RSU'), ('rme', 'RME'), ('rp', 'RP')],
        string="Tipo de manejo",
        default='rsu',
        help="Clasificación oficial del residuo."
    )

    plan_manejo = fields.Selection([
        ('reciclaje', 'Reciclaje'),
        ('coprocesamiento', 'Co-procesamiento'),
        ('tratamiento_fisicoquimico', 'Tratamiento Físico-Químico'),
        ('tratamiento_biologico', 'Tratamiento Biológico'),
        ('tratamiento_termico', 'Tratamiento Térmico'),
        ('confinamiento_controlado', 'Confinamiento Controlado'),
        ('reutilizacion', 'Reutilización'),
        ('destruccion_fiscal', 'Destrucción Fiscal'),
    ], string="Plan de Manejo")

    # -------------------------------------------------------------------------
    # LÓGICA DE EMBALAJE
    # -------------------------------------------------------------------------
    create_new_packaging = fields.Boolean(
        string="¿Nuevo Embalaje?",
        default=False,
        help="Activa para crear un nuevo tipo de embalaje."
    )

    packaging_name = fields.Char(
        string="Nombre Nuevo Embalaje",
        help="Escribe el nombre para crear uno nuevo."
    )

    packaging_id = fields.Many2one(
        'uom.uom',
        string="Embalaje Existente",
        readonly=False,
        help="Selecciona un embalaje existente."
    )

    # -------------------------------------------------------------------------
    # CAPACIDADES Y MEDIDAS
    # -------------------------------------------------------------------------
    capacity = fields.Char(string="Capacidad", help="Capacidad del contenedor (ej: 100 L)")
    weight_kg = fields.Float(string="Peso Total Estimado (kg)", default=0.0)
    volume = fields.Float(string="Número de Unidades", default=1.0)

    weight_per_unit = fields.Float(string="Peso por Unidad (kg)", compute="_compute_weight_per_unit", store=True)

    uom_id = fields.Many2one(
        'uom.uom',
        string="Unidad de Medida Base",
        default=lambda self: self._default_service_uom()
    )

    product_id = fields.Many2one(
        'product.product',
        string="Servicio Asociado",
        readonly=True,
        help="Producto/servicio creado o asociado a partir de este residuo"
    )

    # -------------------------------------------------------------------------
    # COMPUTES / ONCHANGES
    # -------------------------------------------------------------------------
    @api.depends('volume', 'weight_kg')
    def _compute_weight_per_unit(self):
        for record in self:
            record.weight_per_unit = (record.weight_kg / record.volume) if record.volume else 0.0

    @api.onchange('weight_kg', 'volume')
    def _onchange_weight_calculation(self):
        for record in self:
            record.weight_per_unit = (record.weight_kg / record.volume) if record.volume else 0.0

    @api.onchange('create_new_service')
    def _onchange_create_new_service(self):
        if self.create_new_service:
            self.existing_service_id = False
            self.product_id = False
            if not self.uom_id:
                self.uom_id = self._default_service_uom()
        else:
            if not self.existing_service_id:
                self.product_id = False

    @api.onchange('create_new_packaging')
    def _onchange_create_new_packaging(self):
        if self.create_new_packaging:
            self.packaging_id = False
        else:
            self.packaging_name = False

    @api.onchange('existing_service_id')
    def _onchange_existing_service_id(self):
        if self.existing_service_id and not self.create_new_service:
            service = self.existing_service_id
            self.product_id = service.id
            self.name = service.name
            self.uom_id = self._default_service_uom()

            self.create_new_packaging = False
            self.packaging_id = False
            self.packaging_name = False

    # -------------------------------------------------------------------------
    # VALIDACIONES
    # -------------------------------------------------------------------------
    @api.constrains('create_new_service', 'name', 'existing_service_id')
    def _check_service_fields(self):
        for record in self:
            if record.create_new_service and not (record.name or '').strip():
                raise ValidationError("El nombre del residuo es obligatorio cuando se crea un nuevo servicio.")
            if not record.create_new_service and not record.existing_service_id:
                raise ValidationError("Debe seleccionar un servicio existente o marcar '¿Nuevo?'")

    @api.constrains('create_new_packaging', 'packaging_name', 'packaging_id')
    def _check_packaging_fields(self):
        for record in self:
            if record.create_new_packaging or record.packaging_id:
                if record.create_new_packaging and not record.packaging_name:
                    raise ValidationError("Debe escribir un nombre para el nuevo embalaje.")
                if not record.create_new_packaging and not record.packaging_id:
                    raise ValidationError("Debe seleccionar un embalaje existente o marcar '¿Nuevo?'")

    def _create_or_update_packaging_v19(self, record):
        """
        Crea una UdM para "embalaje" si el usuario eligió crear nuevo.
        Robusto para Odoo 19: no asumimos category_id; copiamos estructura desde "Unidades".
        """
        if not record.create_new_packaging or not record.packaging_name:
            return

        UoM = self.env['uom.uom'].sudo()
        existing = UoM.search([('name', '=', record.packaging_name)], limit=1)
        if existing:
            record.packaging_id = existing.id
            return

        unit = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

        vals = {'name': record.packaging_name}

        # Copiar campos compatibles desde unit (si existe)
        if unit:
            for f in ['category_id', 'uom_type', 'rounding', 'active', 'relative_uom_id', 'factor', 'factor_inv', 'ratio', 'ratio_inv']:
                if f in unit._fields and f in UoM._fields:
                    vals[f] = unit[f]

        qty = record.volume or 1.0

        # Ajustar el "factor/ratio" solo si el campo existe
        if 'factor' in UoM._fields:
            vals['factor'] = (1.0 / qty) if qty else 1.0
        elif 'ratio' in UoM._fields:
            vals['ratio'] = (1.0 / qty) if qty else 1.0

        if 'active' in UoM._fields:
            vals['active'] = True

        try:
            new_uom = UoM.create(vals)
            record.packaging_id = new_uom.id
        except Exception as e:
            _logger.exception("Error al crear embalaje (UoM). vals=%s", vals)
            raise ValidationError(f"No se pudo crear el embalaje (UdM). Detalle: {str(e)}")

    # -------------------------------------------------------------------------
    # CREATE / WRITE
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        default_uom = self._default_service_uom()
        for vals in vals_list:
            if not vals.get('uom_id') and default_uom:
                vals['uom_id'] = default_uom.id

        records = super().create(vals_list)

        for record in records:
            # 1) Servicio
            if not record.create_new_service and record.existing_service_id:
                record.product_id = record.existing_service_id.id

            elif record.create_new_service and (record.name or '').strip():
                service = record.lead_id._create_service_from_residue(record)
                record.product_id = service.id

            # 2) Embalaje
            record._create_or_update_packaging_v19(record)

        return records

    def write(self, vals):
        result = super().write(vals)

        for record in self:
            if 'existing_service_id' in vals:
                if not record.create_new_service and record.existing_service_id:
                    record.product_id = record.existing_service_id.id

            # Si se activó "Nuevo" o se llenó name después, aquí también lo crea
            if record.create_new_service and not record.product_id and (record.name or '').strip():
                service = record.lead_id._create_service_from_residue(record)
                record.product_id = service.id

            if 'create_new_packaging' in vals or 'packaging_name' in vals:
                record._create_or_update_packaging_v19(record)

        return result
