-e ### ./models/crm_lead.py
```
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
        service_name = f"Servicio Recolección de {residue.name}"
        
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
        domain="[('type', '=', 'service'), ('categ_id.name', 'ilike', 'servicios de residuos')]",
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
    
    # AGREGAR VALIDACIÓN PERSONALIZADA
    @api.constrains('create_new_service', 'name', 'residue_type', 'plan_manejo', 'existing_service_id', 'weight_kg', 'volume')
    def _check_required_fields(self):
        """Validar campos requeridos según el modo de creación"""
        for record in self:
            if record.create_new_service:
                # Si crea nuevo servicio, validar campos requeridos
                if not record.name:
                    raise ValidationError("El nombre del residuo es obligatorio cuando se crea un nuevo servicio.")
                if not record.residue_type:
                    raise ValidationError("El tipo de residuo es obligatorio cuando se crea un nuevo servicio.")
                if not record.plan_manejo:
                    raise ValidationError("El plan de manejo es obligatorio cuando se crea un nuevo servicio.")
                if not record.weight_kg or record.weight_kg <= 0:
                    raise ValidationError("El peso total en kg debe ser mayor a cero.")
                if not record.volume or record.volume <= 0:
                    raise ValidationError("El número de unidades debe ser mayor a cero.")
            else:
                # Si usa servicio existente, validar que haya seleccionado uno
                if not record.existing_service_id:
                    raise ValidationError("Debe seleccionar un servicio existente o marcar 'Crear Nuevo Servicio'.")
    
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
            elif record.create_new_service and ('name' in vals or 'plan_manejo' in vals or 'weight_kg' in vals):
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
Peso estimado: {record.weight_kg} kg
Unidades: {record.volume} {record.uom_id.name if record.uom_id else ''}""",
                        })
                    except Exception:
                        pass
        return result
```

-e ### ./salida_modulo_completo.md
```
-e ### ./models/crm_lead.py
```
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
        service_name = f"Servicio Recolección de {residue.name}"
        
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
        domain="[('type', '=', 'service'), ('categ_id.name', 'ilike', 'servicios de residuos')]",
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
    
    # AGREGAR VALIDACIÓN PERSONALIZADA
    @api.constrains('create_new_service', 'name', 'residue_type', 'plan_manejo', 'existing_service_id', 'weight_kg', 'volume')
    def _check_required_fields(self):
        """Validar campos requeridos según el modo de creación"""
        for record in self:
            if record.create_new_service:
                # Si crea nuevo servicio, validar campos requeridos
                if not record.name:
                    raise ValidationError("El nombre del residuo es obligatorio cuando se crea un nuevo servicio.")
                if not record.residue_type:
                    raise ValidationError("El tipo de residuo es obligatorio cuando se crea un nuevo servicio.")
                if not record.plan_manejo:
                    raise ValidationError("El plan de manejo es obligatorio cuando se crea un nuevo servicio.")
                if not record.weight_kg or record.weight_kg <= 0:
                    raise ValidationError("El peso total en kg debe ser mayor a cero.")
                if not record.volume or record.volume <= 0:
                    raise ValidationError("El número de unidades debe ser mayor a cero.")
            else:
                # Si usa servicio existente, validar que haya seleccionado uno
                if not record.existing_service_id:
                    raise ValidationError("Debe seleccionar un servicio existente o marcar 'Crear Nuevo Servicio'.")
    
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
            elif record.create_new_service and ('name' in vals or 'plan_manejo' in vals or 'weight_kg' in vals):
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
Peso estimado: {record.weight_kg} kg
Unidades: {record.volume} {record.uom_id.name if record.uom_id else ''}""",
                        })
                    except Exception:
                        pass
        return result
```
```

-e ### ./security/ir.model.access.csv
```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_crm_lead_residue_user,access_crm_lead_residue_user,model_crm_lead_residue,sales_team.group_sale_salesman,1,1,1,1
access_crm_lead_residue_manager,access_crm_lead_residue_manager,model_crm_lead_residue,sales_team.group_sale_manager,1,1,1,1
access_crm_lead_residue_salesman_all_leads,access_crm_lead_residue_salesman_all_leads,model_crm_lead_residue,sales_team.group_sale_salesman_all_leads,1,1,1,1
```

-e ### ./views/crm_lead_view.xml
```
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <record id="view_crm_lead_form_custom_fields" model="ir.ui.view">
        <field name="name">crm.lead.form.custom.fields</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_lead_view_form"/>
        <field name="arch" type="xml">
            <xpath expr="//page[@name='extra']" position="after">

                 <!-- Página de Validaciones -->
                <page string="Validaciones" name="validaciones">
                    
                    <!-- Sección de Residuo Nuevo -->
                    <group string="Validación de Residuo Nuevo">
                        <field name="residue_new"/>
                        
                        <div invisible="not show_sample_alert" style="margin: 10px 0;">
                            <div class="alert alert-warning" role="alert">
                                <i class="fa fa-warning"/> 
                                <strong>Atención:</strong> Se requiere solicitar muestra al cliente para análisis.
                            </div>
                        </div>

                        <field name="sample_result_file"
                               filename="sample_result_filename"
                               widget="pdf_viewer"
                               invisible="not residue_new"
                               options="{'force_save': True}"/>
                        
                        <field name="sample_result_filename" invisible="1"/>
                    </group>

                    <!-- Sección de Visita Presencial -->
                    <group string="Validación de Visita Presencial">
                        <field name="requiere_visita"/>

                        <div invisible="not show_visita_alert" style="margin: 10px 0;">
                            <div class="alert alert-warning" role="alert">
                                <i class="fa fa-warning"/> 
                                <strong>Atención:</strong> Se requiere validar residuos y volúmenes en sitio y subir el informe correspondiente.
                            </div>
                        </div>

                        <field name="visita_validation_file"
                               filename="visita_validation_filename"
                               widget="pdf_viewer"
                               invisible="not requiere_visita"
                               options="{'force_save': True}"/>
                        
                        <field name="visita_validation_filename" invisible="1"/>
                    </group>

                    <!-- Campos computados ocultos -->
                    <field name="show_sample_alert" invisible="1"/>
                    <field name="show_visita_alert" invisible="1"/>
                    
                </page>

                <!-- Página de Residuos -->
                <page string="Residuos" name="residuos">
                    <separator string="Gestión de Residuos"/>
                    <field name="residue_line_ids">
                        <list editable="bottom">
                            <field name="create_new_service" string="Crear Nuevo"/>
                            <field name="existing_service_id" 
                                   string="Servicio Existente" 
                                   options="{'no_create': True}"
                                   context="{'tree_view_ref': 'product.product_product_tree_view'}"/>
                            <field name="name" 
                                   string="Nombre del Residuo" 
                                   placeholder="Ingrese el nombre del residuo..."/>
                            <field name="residue_type" 
                                   string="Tipo"/>
                            <field name="plan_manejo" 
                                   string="Plan de Manejo"/>
                            <field name="weight_kg" string="Peso Total (kg)" placeholder="0.00"/>
                            <field name="volume" string="Unidades" placeholder="1"/>
                            <field name="weight_per_unit" string="Kg/Unidad" readonly="1"/>
                            <field name="uom_id" string="Unidad" options="{'no_create': True}"/>
                            <field name="product_id" string="Servicio Generado" readonly="1"/>
                            <button name="%(product.product_template_action)d"
                                    type="action"
                                    icon="fa-external-link"
                                    title="Ver servicio"
                                    context="{'search_default_id': product_id}"
                                    invisible="not product_id"/>
                        </list>
                        
                        <!-- Vista de formulario para edición detallada -->
                        <form>
                            <group>
                                <group string="Modo de Servicio">
                                    <field name="create_new_service"/>
                                </group>
                                
                                <!-- Selección de servicio existente -->
                                <group string="Servicio Existente" invisible="create_new_service">
                                    <field name="existing_service_id" 
                                           options="{'no_create': True}"
                                           placeholder="Buscar servicio existente..."/>
                                    <separator string="Información extraída del servicio" colspan="2" invisible="not existing_service_id"/>
                                    <field name="name" string="Nombre" readonly="not create_new_service" invisible="not existing_service_id"/>
                                    <field name="residue_type" string="Tipo de Residuo" readonly="not create_new_service" invisible="not existing_service_id"/>
                                    <field name="plan_manejo" string="Plan de Manejo" readonly="not create_new_service" invisible="not existing_service_id"/>
                                </group>
                                
                                <!-- Creación de nuevo servicio -->
                                <group string="Nuevo Servicio" invisible="not create_new_service">
                                    <field name="name" placeholder="Nombre del residuo"/>
                                    <field name="residue_type"/>
                                    <field name="plan_manejo"/>
                                </group>
                                
                                <!-- Información de cantidades y peso - SIEMPRE EDITABLE -->
                                <group string="Cantidades y Peso">
                                    <field name="weight_kg" string="Peso Total (kg)" placeholder="Ejemplo: 200"/>
                                    <field name="volume" string="Número de Unidades" placeholder="Ejemplo: 1"/>
                                    <field name="weight_per_unit" string="Kg por Unidad" readonly="1"/>
                                    <field name="uom_id" options="{'no_create': True}"/>
                                    <field name="product_id" readonly="1"/>
                                </group>
                            </group>
                        </form>
                    </field>
                </page>

                <!-- Página de Información del Servicio -->
                <page string="Información del Servicio" name="service_info">
                    <group>
                        <group string="Detalles del Servicio">
                            <field name="pickup_location"/>
                            <field name="service_frequency"/>
                        </group>
                    </group>
                </page>
                
                <!-- Página de Información Básica del Prospecto -->
                <page string="Información del Prospecto" name="prospect_info">
                    <group>
                        <group string="Información Básica del Prospecto">
                            <field name="company_size"/>
                            <field name="industrial_sector"/>
                        </group>
                        
                        <group string="Clasificación Comercial">
                            <field name="prospect_priority"/>
                            <field name="estimated_business_potential"/>
                        </group>
                    </group>
                </page>

                <!-- Página de Información Operativa -->
                <page string="Información Operativa" name="operational_info">
                    <group>
                        <group string="Condiciones Operativas">
                            <field name="access_restrictions" widget="text"/>
                            <field name="allowed_collection_schedules" widget="text"/>
                            <field name="current_container_types" widget="text"/>
                            <field name="special_handling_conditions" widget="text"/>
                            <field name="seasonality" widget="text"/>
                        </group>
                    </group>
                </page>

                <!-- Página de Información Regulatoria -->
                <page string="Información Regulatoria" name="regulatory_info">
                    <group>
                        <group string="Registros y Autorizaciones">
                            <field name="waste_generator_registration"/>
                            <field name="environmental_authorizations" widget="text"/>
                            <field name="quality_certifications" widget="text"/>
                            <field name="other_relevant_permits" widget="text"/>
                        </group>
                    </group>
                </page>

                <!-- Página de Competencia y Mercado -->
                <page string="Competencia y Mercado" name="competition_market">
                    <group>
                        <group string="Proveedor Actual">
                            <field name="current_service_provider"/>
                            <field name="current_costs"/>
                            <field name="current_provider_satisfaction"/>
                            <field name="reason_for_new_provider" widget="text"/>
                        </group>
                    </group>
                </page>

                <!-- Página de Requerimientos Especiales -->
                <page string="Requerimientos Especiales" name="special_requirements">
                    <group>
                        <group string="Requerimientos del Cliente">
                            <field name="specific_certificates_needed" widget="text"/>
                            <field name="reporting_requirements" widget="text"/>
                            <field name="service_urgency"/>
                            <field name="estimated_budget"/>
                        </group>
                    </group>
                </page>

                <!-- Página de Seguimiento -->
                <page string="Seguimiento" name="seguimiento">
                    <group>
                        <group string="Gestión de Seguimiento">
                            <field name="next_contact_date"/>
                            <field name="pending_actions" widget="text"/>
                            <field name="conversation_notes" widget="text"/>
                        </group>
                    </group>
                </page>

            </xpath>
        </field>
    </record>
</odoo>
```

### __init__.py
```python
from . import models
```

### __manifest__.py
```python
{
    'name': 'CRM Custom Fields',
    'version': '18.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'Añade campos personalizados en oportunidades CRM.',
    'author': 'Alphaqueb Consulting',
    'depends': [
        'crm',
        'uom',
        'product',
        'sale_management',  # AGREGADO: necesario para funcionalidad de ventas
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

