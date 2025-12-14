# models/crm_lead.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # INFORMACIÓN BÁSICA DEL PROSPECTO
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

    # Campos de información del servicio (existentes)
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
    pickup_location = fields.Char(
        string="Ubicación de recolección",
        help="Dirección exacta (planta, almacén, muelle, etc.) donde se retira el residuo."
    )
    
    # Campos de residuos (existentes)
    residue_line_ids = fields.One2many('crm.lead.residue', 'lead_id', string="Listado de Residuos")
    
    # Campos de validación de residuo nuevo (existentes)
    residue_new = fields.Boolean(string="¿Residuo Nuevo?")
    show_sample_alert = fields.Boolean(
        string="Mostrar alerta de muestra",
        compute="_compute_show_sample_alert",
        store=True
    )
    sample_result_file = fields.Binary(string="Archivo de Resultados de Muestra")
    sample_result_filename = fields.Char(string="Nombre del Archivo de Resultados de Muestra")
    
    # Campos de validación de visita presencial (existentes)
    requiere_visita = fields.Boolean(string="Requiere visita presencial")
    show_visita_alert = fields.Boolean(
        string="Mostrar alerta visita",
        compute="_compute_show_visita_alert",
        store=True
    )
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
        """Crear un producto de tipo servicio desde un residue"""
        category = self.env['product.category'].search([
            ('name', 'ilike', 'servicios de residuos')
        ], limit=1)
        
        if not category:
            category = self.env['product.category'].create({
                'name': 'Servicios de Residuos',
            })

        service_name = f"{residue.name}"
        
        return self.env['product.product'].create({
            'name': service_name,
            'type': 'service',
            'categ_id': category.id,
            'sale_ok': True,
            'purchase_ok': False,
            'description_sale': f"""Servicio de manejo de residuo: {residue.name}
Plan de manejo: {dict(residue._fields['plan_manejo'].selection).get(residue.plan_manejo, '')}
Tipo de residuo: {dict(residue._fields['residue_type'].selection).get(residue.residue_type, '')}
Capacidad: {residue.capacity}
Peso estimado: {residue.weight_kg} kg
Unidades: {residue.volume} {residue.uom_id.name if residue.uom_id else ''}""",
            'default_code': f"SRV-{residue.residue_type.upper()}-{residue.id}",
        })


class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

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
    # LÓGICA DE EMBALAJE (CORREGIDA)
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
    
    weight_kg = fields.Float(
        string="Peso Total Estimado (kg)",
        default=0.0
    )
    
    volume = fields.Float(
        string="Número de Unidades",
        default=1.0
    )
    
    weight_per_unit = fields.Float(
        string="Peso por Unidad (kg)",
        compute="_compute_weight_per_unit",
        store=True
    )
    
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unidad de Medida Base",
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    )
    
    product_id = fields.Many2one(
        'product.product', 
        string="Servicio Asociado",
        readonly=True,
        help="Producto/servicio creado o asociado a partir de este residuo"
    )

    # -------------------------------------------------------------------------
    # MÉTODOS COMPUTE Y ONCHANGE
    # -------------------------------------------------------------------------

    @api.depends('volume', 'weight_kg')
    def _compute_weight_per_unit(self):
        """Calcular peso promedio por unidad"""
        for record in self:
            if record.volume and record.volume > 0:
                record.weight_per_unit = record.weight_kg / record.volume
            else:
                record.weight_per_unit = 0.0
    
    @api.onchange('weight_kg', 'volume')
    def _onchange_weight_calculation(self):
        """Validar coherencia entre peso y unidades"""
        for record in self:
            if record.weight_kg and record.volume:
                record.weight_per_unit = record.weight_kg / record.volume
    
    @api.onchange('create_new_service')
    def _onchange_create_new_service(self):
        """Limpiar campos de servicio según el switch"""
        if self.create_new_service:
            self.existing_service_id = False
            self.product_id = False
            if not self.uom_id:
                self.uom_id = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        else:
            # Si desmarca nuevo, se limpia el servicio asociado para obligar a seleccionar
            if not self.existing_service_id:
                self.product_id = False

    @api.onchange('create_new_packaging')
    def _onchange_create_new_packaging(self):
        """Limpiar campos de embalaje según el switch"""
        if self.create_new_packaging:
            self.packaging_id = False
        else:
            self.packaging_name = False

    @api.onchange('existing_service_id')
    def _onchange_existing_service_id(self):
        """Cargar información al seleccionar servicio existente"""
        if self.existing_service_id and not self.create_new_service:
            service = self.existing_service_id
            
            self.product_id = service.id
            self.name = service.name
            self.uom_id = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            
            # Limpiamos selección previa de embalaje
            self.create_new_packaging = False
            self.packaging_id = False
            self.packaging_name = False
            
            # Lógica de extracción de datos...
            if service.default_code:
                parts = service.default_code.split('-')
                if len(parts) >= 2:
                    residue_type_map = {'PELIGROSO': 'peligroso', 'NO_PELIGROSO': 'no_peligroso', 'ESPECIAL': 'especial'}
                    tipo_upper = parts[1].upper()
                    if tipo_upper in residue_type_map:
                        self.residue_type = residue_type_map[tipo_upper]
            
            description = (service.description_sale or '').lower()
            if 'capacidad:' in description:
                try:
                    capacity_text = description.split('capacidad:')[1].split('l')[0].strip()
                    self.capacity = float(capacity_text)
                except:
                    pass
            
            plan_map = {
                'reciclaje': 'reciclaje',
                'co-procesamiento': 'coprocesamiento', 
                'coprocesamiento': 'coprocesamiento',
                'físico-químico': 'tratamiento_fisicoquimico',
                'fisicoquimico': 'tratamiento_fisicoquimico',
                'biológico': 'tratamiento_biologico',
                'biologico': 'tratamiento_biologico',
                'térmico': 'tratamiento_termico',
                'termico': 'tratamiento_termico',
                'incineración': 'tratamiento_termico',
                'incineracion': 'tratamiento_termico',
                'confinamiento': 'confinamiento_controlado',
                'reutilización': 'reutilizacion',
                'reutilizacion': 'reutilizacion',
                'destrucción': 'destruccion_fiscal',
                'destruccion': 'destruccion_fiscal',
            }
            
            for key, value in plan_map.items():
                if key in description:
                    self.plan_manejo = value
                    break
    
    # -------------------------------------------------------------------------
    # VALIDACIONES Y CREACIÓN
    # -------------------------------------------------------------------------

    @api.constrains('create_new_service', 'name', 'existing_service_id')
    def _check_service_fields(self):
        """Validar campos requeridos para Servicio"""
        for record in self:
            if record.create_new_service and not record.name:
                raise ValidationError("El nombre del residuo es obligatorio cuando se crea un nuevo servicio.")
            if not record.create_new_service and not record.existing_service_id:
                raise ValidationError("Debe seleccionar un servicio existente o marcar '¿Nuevo?'")

    @api.constrains('create_new_packaging', 'packaging_name', 'packaging_id')
    def _check_packaging_fields(self):
        """Validar campos requeridos para Embalaje"""
        for record in self:
            # Solo validamos si hay intención de llenar la línea (ej. si hay peso o volumen)
            # O si explícitamente se usó alguno de los campos de embalaje
            if record.create_new_packaging or record.packaging_id:
                if record.create_new_packaging and not record.packaging_name:
                    raise ValidationError("Debe escribir un nombre para el nuevo embalaje.")
                if not record.create_new_packaging and not record.packaging_id:
                     raise ValidationError("Debe seleccionar un embalaje existente o marcar '¿Nuevo?'")

    def _create_or_update_packaging_v19(self, record):
        """
        Lógica para crear UoM.
        Se ejecuta solo si create_new_packaging es True.
        """
        if not record.create_new_packaging or not record.packaging_name:
            return

        # Evitar crear si ya existe con el mismo nombre
        domain = [('name', '=', record.packaging_name)]
        existing = self.env['uom.uom'].search(domain, limit=1)

        if existing:
            record.packaging_id = existing.id
        else:
            try:
                # Calculamos el factor (inverso de la cantidad)
                qty = record.volume or 1.0
                factor = 1.0 / qty if qty != 0 else 1.0
                
                vals = {
                    'name': record.packaging_name,
                    'factor': factor,
                    'active': True,
                    # Intentamos asignar categoría por defecto (Unidad)
                    'category_id': self.env.ref('uom.product_uom_categ_unit').id
                }
                
                if 'relative_uom_id' in self.env['uom.uom']._fields and record.uom_id:
                    vals['relative_uom_id'] = record.uom_id.id
                    
                new_uom = self.env['uom.uom'].create(vals)
                record.packaging_id = new_uom.id
                
            except Exception as e:
                _logger.warning(f"Error al crear embalaje (UoM): {str(e)}")

    @api.model_create_multi
    def create(self, vals_list):
        uom_unit = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        for vals in vals_list:
            if not vals.get('uom_id') and uom_unit:
                vals['uom_id'] = uom_unit.id
        
        records = super().create(vals_list)
        
        for record in records:
            # 1. Gestión del Servicio
            if not record.create_new_service and record.existing_service_id:
                record.product_id = record.existing_service_id.id
            elif record.create_new_service and record.name:
                try:
                    service = record.lead_id._create_service_from_residue(record)
                    record.product_id = service.id
                except Exception as e:
                    _logger.warning(f"Error al crear servicio: {str(e)}")
            
            # 2. Gestión del Embalaje
            self._create_or_update_packaging_v19(record)
        
        return records
    
    def write(self, vals):
        result = super().write(vals)
        for record in self:
            # 1. Gestión del Servicio
            if 'existing_service_id' in vals:
                if not record.create_new_service and record.existing_service_id:
                    record.product_id = record.existing_service_id.id
            
            elif record.create_new_service and not record.product_id and record.name:
                try:
                    service = record.lead_id._create_service_from_residue(record)
                    record.product_id = service.id
                except Exception as e:
                    _logger.warning(f"Error al crear servicio: {str(e)}")

            # 2. Gestión del Embalaje
            if 'create_new_packaging' in vals or 'packaging_name' in vals:
                self._create_or_update_packaging_v19(record)
        
        return result