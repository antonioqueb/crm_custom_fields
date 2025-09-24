# models/crm_lead.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError

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
        # Obtener categoría para servicios de residuos (o crear una)
        category = self.env['product.category'].search([
            ('name', 'ilike', 'servicios de residuos')
        ], limit=1)
        
        if not category:
            category = self.env['product.category'].create({
                'name': 'Servicios de Residuos',
            })

        # Crear el producto/servicio
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
Peso estimado: {residue.weight_kg} kg
Unidades: {residue.volume} {residue.uom_id.name if residue.uom_id else ''}""",
            'default_code': f"SRV-{residue.residue_type.upper()}-{residue.id}",
        })


class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

    lead_id = fields.Many2one('crm.lead', string="Lead/Oportunidad", required=True, ondelete='cascade')
    name = fields.Char(string="Residuo")  # QUITADO required=True temporalmente
    volume = fields.Float(string="Unidades", default=1.0)  # MODIFICADO: ahora es "Unidades"
    
    # NUEVO CAMPO PARA PESO
    weight_kg = fields.Float(
        string="Peso Total (kg)",
        help="Peso total del residuo en kilogramos. Este valor se usará para el sistema de acopio."
    )
    
    # CAMPO COMPUTADO PARA MOSTRAR CONVERSIÓN
    weight_per_unit = fields.Float(
        string="Kg por Unidad",
        compute="_compute_weight_per_unit",
        store=True,
        help="Peso promedio por unidad (kg/unidad)"
    )
    
    uom_id = fields.Many2one('uom.uom', string="Unidad de Medida")  # QUITADO required=True temporalmente
    
    # CAMBIO IMPORTANTE: hacer residue_type no requerido cuando se usa servicio existente
    residue_type = fields.Selection(
        selection=[('rsu', 'RSU'), ('rme', 'RME'), ('rp', 'RP')],
        string="Tipo de manejo",
        default='rsu',  # MANTENER default
        help="Clasificación oficial del residuo: RSU (Sólido Urbano), RME (Manejo Especial) o RP (Peligroso)."
    )

    plan_manejo = fields.Selection(
        selection=[
            ('reciclaje', 'Reciclaje'),
            ('coprocesamiento', 'Co-procesamiento'),
            ('tratamiento_fisicoquimico', 'Tratamiento Físico-Químico'),
            ('tratamiento_biologico', 'Tratamiento Biológico'),
            ('tratamiento_termico', 'Tratamiento Térmico (Incineración)'),
            ('confinamiento_controlado', 'Confinamiento Controlado'),
            ('reutilizacion', 'Reutilización'),
            ('destruccion_fiscal', 'Destrucción Fiscal'),
        ],
        string="Plan de Manejo",
        help="Método de tratamiento y/o disposición final para el residuo según normatividad ambiental."
    )
    
    product_id = fields.Many2one(
        'product.product', 
        string="Servicio Asociado",
        readonly=True,
        help="Producto/servicio creado automáticamente a partir de este residuo"
    )

    # Campo para seleccionar servicio existente
    existing_service_id = fields.Many2one(
        'product.product',
        string="Seleccionar Servicio Existente",
        domain=[('sale_ok', '=', True), ('type', '=', 'service')],
        help="Selecciona un servicio existente en lugar de crear uno nuevo"
    )

    # Campo para decidir si crear o seleccionar
    create_new_service = fields.Boolean(
        string="Crear Nuevo Servicio",
        default=True,
        help="Marca para crear un nuevo servicio, desmarca para seleccionar uno existente"
    )
    
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
                # Calcular automáticamente el peso por unidad
                record.weight_per_unit = record.weight_kg / record.volume
    
    @api.onchange('create_new_service')
    def _onchange_create_new_service(self):
        """Limpiar campos según la opción seleccionada"""
        if self.create_new_service:
            # Si cambia a crear nuevo servicio, limpiar servicio existente
            self.existing_service_id = False
            # Mantener otros campos para que el usuario pueda editarlos
        else:
            # Si cambia a usar servicio existente, NO limpiar campos inmediatamente
            # Los campos se actualizarán cuando seleccione un servicio
            pass

    @api.onchange('existing_service_id')
    def _onchange_existing_service_id(self):
        """Actualizar información del residuo basado en el servicio seleccionado"""
        if self.existing_service_id and not self.create_new_service:
            # Extraer información del servicio seleccionado
            service = self.existing_service_id
            self.name = service.name
            self.product_id = service.id
            
            # Intentar extraer información del código del producto o descripción
            if service.default_code:
                # Ejemplo: SRV-RSU-123 -> extraer RSU
                parts = service.default_code.split('-')
                if len(parts) >= 2:
                    residue_type_map = {'RSU': 'rsu', 'RME': 'rme', 'RP': 'rp'}
                    if parts[1] in residue_type_map:
                        self.residue_type = residue_type_map[parts[1]]
            
            # Intentar extraer plan de manejo de la descripción o nombre
            description = (service.description_sale or service.name or '').lower()
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
    
    # VALIDACIÓN PERSONALIZADA RELAJADA PARA PROSPECCIÓN
    @api.constrains('create_new_service', 'name', 'existing_service_id')
    def _check_required_fields(self):
        """Validar campos requeridos según el modo de creación"""
        for record in self:
            if record.create_new_service:
                # En prospección, sólo obligamos nombre del residuo
                if not record.name:
                    raise ValidationError("El nombre del residuo es obligatorio cuando se crea un nuevo servicio.")
            else:
                # Si usa servicio existente, validar que haya seleccionado uno
                if not record.existing_service_id:
                    raise ValidationError("Debe seleccionar un servicio existente o marcar 'Crear Nuevo Servicio'.")
    
    @api.model_create_multi
    def create(self, vals_list):
        """Crear servicios automáticamente al crear residuos cuando ya hay datos suficientes"""
        records = super().create(vals_list)
        for record in records:
            if not record.create_new_service and record.existing_service_id:
                # Usar servicio existente
                record.product_id = record.existing_service_id.id
            elif record.create_new_service and record.name and record.plan_manejo and not record.product_id:
                # Crear nuevo servicio si ya hay plan de manejo definido
                try:
                    service = record.lead_id._create_service_from_residue(record)
                    record.product_id = service.id
                except Exception:
                    # Si falla la creación del servicio, continúa sin bloquear
                    pass
        return records
    
    def write(self, vals):
        """Crear o actualizar servicios al modificar residuos"""
        result = super().write(vals)
        for record in self:
            # Si cambia a usar servicio existente
            if 'existing_service_id' in vals and not record.create_new_service:
                record.product_id = record.existing_service_id.id
            # Si cambia a crear nuevo servicio
            elif 'create_new_service' in vals and record.create_new_service:
                if record.name and record.plan_manejo and not record.product_id:
                    try:
                        service = record.lead_id._create_service_from_residue(record)
                        record.product_id = service.id
                    except Exception:
                        pass
            # Si se modifican campos importantes y es nuevo servicio
            elif record.create_new_service and ('name' in vals or 'plan_manejo' in vals or 'weight_kg' in vals):
                if not record.product_id and record.name and record.plan_manejo:
                    try:
                        service = record.lead_id._create_service_from_residue(record)
                        record.product_id = service.id
                    except Exception:
                        pass
                elif record.product_id:
                    # Actualizar servicio existente generado
                    try:
                        service_name = f"Servicio de {record.name} - {dict(record._fields['plan_manejo'].selection).get(record.plan_manejo, '')}"
                        record.product_id.write({
                            'name': service_name,
                            'description_sale': f"""Servicio de manejo de residuo: {record.name}
Plan de manejo: {dict(record._fields['plan_manejo'].selection).get(record.plan_manejo, '')}
Tipo de residuo: {dict(record._fields['residue_type'].selection).get(record.residue_type, '')}
Peso estimado: {record.weight_kg} kg
Unidades: {record.volume} {record.uom_id.name if record.uom_id else ''}""",
                        })
                    except Exception:
                        pass
        return result
