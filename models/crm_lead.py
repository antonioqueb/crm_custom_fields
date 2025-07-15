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
        service_name = f"Servicio de Recolección de {residue.name} - {dict(residue._fields['plan_manejo'].selection).get(residue.plan_manejo, '')}"
        
        return self.env['product.product'].create({
            'name': service_name,
            'type': 'service',
            'categ_id': category.id,
            'sale_ok': True,
            'purchase_ok': False,
            'description_sale': f"""Servicio de manejo de residuo: {residue.name}
Plan de manejo: {dict(residue._fields['plan_manejo'].selection).get(residue.plan_manejo, '')}
Tipo de residuo: {dict(residue._fields['residue_type'].selection).get(residue.residue_type, '')}
Volumen: {residue.volume} {residue.uom_id.name}""",
            'default_code': f"SRV-{residue.residue_type.upper()}-{residue.id}",
        })


class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

    lead_id = fields.Many2one('crm.lead', string="Lead/Oportunidad", required=True, ondelete='cascade')
    name = fields.Char(string="Residuo", required=True)
    volume = fields.Float(string="Volumen", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unidad de Medida", required=True)
    residue_type = fields.Selection(
        selection=[('rsu', 'RSU'), ('rme', 'RME'), ('rp', 'RP')],
        string="Tipo de manejo",
        required=True,
        default='rsu',
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

    # NUEVO: Campo para seleccionar servicio existente
    existing_service_id = fields.Many2one(
        'product.product',
        string="Seleccionar Servicio Existente",
        domain="[('type', '=', 'service'), ('categ_id.name', 'ilike', 'servicios de residuos')]",
        help="Selecciona un servicio existente en lugar de crear uno nuevo"
    )

    # NUEVO: Campo para decidir si crear o seleccionar
    create_new_service = fields.Boolean(
        string="Crear Nuevo Servicio",
        default=True,
        help="Marca para crear un nuevo servicio, desmarca para seleccionar uno existente"
    )
    
    @api.onchange('create_new_service')
    def _onchange_create_new_service(self):
        """Limpiar campos según la opción seleccionada"""
        if self.create_new_service:
            self.existing_service_id = False
        else:
            self.name = False
            self.plan_manejo = False
            self.residue_type = False

    @api.onchange('existing_service_id')
    def _onchange_existing_service_id(self):
        """Actualizar información del residuo basado en el servicio seleccionado"""
        if self.existing_service_id and not self.create_new_service:
            # Intentar extraer información del nombre del servicio
            service_name = self.existing_service_id.name
            self.name = service_name
            # Copiar información básica
            self.product_id = self.existing_service_id.id
    
    @api.model_create_multi
    def create(self, vals_list):
        """Crear servicios automáticamente al crear residuos"""
        records = super().create(vals_list)
        for record in records:
            if not record.create_new_service and record.existing_service_id:
                # Usar servicio existente
                record.product_id = record.existing_service_id.id
            elif record.create_new_service and record.name and record.plan_manejo and not record.product_id:
                # Crear nuevo servicio
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
            elif record.create_new_service and ('name' in vals or 'plan_manejo' in vals):
                if not record.product_id and record.name and record.plan_manejo:
                    try:
                        service = record.lead_id._create_service_from_residue(record)
                        record.product_id = service.id
                    except Exception:
                        pass
                elif record.product_id:
                    # Actualizar servicio existente
                    try:
                        service_name = f"Servicio de {record.name} - {dict(record._fields['plan_manejo'].selection).get(record.plan_manejo, '')}"
                        record.product_id.write({
                            'name': service_name,
                            'description_sale': f"""Servicio de manejo de residuo: {record.name}
Plan de manejo: {dict(record._fields['plan_manejo'].selection).get(record.plan_manejo, '')}
Tipo de residuo: {dict(record._fields['residue_type'].selection).get(record.residue_type, '')}
Volumen: {record.volume} {record.uom_id.name if record.uom_id else ''}""",
                        })
                    except Exception:
                        pass
        return result