## ./__init__.py
```py
from . import models
```

## ./__manifest__.py
```py
{
    'name': 'CRM Custom Fields',
    'version': '19.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'Añade campos personalizados en oportunidades CRM.',
    'author': 'Alphaqueb Consulting',
    'depends': [
        'crm',
        'uom',
        'product',
        'sale_management', 
        'stock' 
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}```

## ./models/__init__.py
```py
from . import crm_lead
```

## ./models/crm_lead.py
```py
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
Capacidad: {residue.capacity}
Peso estimado: {residue.weight_kg} kg
Unidades: {residue.volume} {residue.uom_id.name if residue.uom_id else ''}""",
            'default_code': f"SRV-{residue.residue_type.upper()}-{residue.id}",
        })


class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

    lead_id = fields.Many2one('crm.lead', string="Lead/Oportunidad", required=True, ondelete='cascade')
    
    # Campo para decidir si es nuevo o existente
    create_new_service = fields.Boolean(
        string="¿Es Nuevo?",
        default=False,
        help="Marca si es un servicio NUEVO que se va a crear. Desmarca si vas a seleccionar un servicio EXISTENTE."
    )
    
    # Campo para seleccionar servicio existente
    existing_service_id = fields.Many2one(
        'product.product',
        string="Servicio Existente",
        domain=[('sale_ok', '=', True), ('type', '=', 'service')],
        help="Selecciona un servicio existente del catálogo"
    )
    
    name = fields.Char(
        string="Nombre del Residuo/Servicio",
        required=False,
        help="Nombre descriptivo del residuo o servicio"
    )
    
    residue_type = fields.Selection(
        selection=[('rsu', 'RSU'), ('rme', 'RME'), ('rp', 'RP')],
        string="Tipo de manejo",
        default='rsu',
        help="Clasificación oficial del residuo: RSU (Sólido Urbano), RME (Manejo Especial) o RP (Peligroso)."
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
    
    capacity = fields.Char(string="Capacidad", help="Capacidad del contenedor (ej: 100 L, 200 Kg, 50 CM³)")
    
    weight_kg = fields.Float(
        string="Peso Total Estimado (kg)",
        default=0.0,
        help="Peso total estimado de todos los contenedores juntos"
    )
    
    volume = fields.Float(
        string="Número de Unidades/Contenedores",
        default=1.0,
        help="Cantidad de contenedores o unidades"
    )
    
    weight_per_unit = fields.Float(
        string="Peso por Unidad (kg)",
        compute="_compute_weight_per_unit",
        store=True,
        help="Peso promedio por unidad (calculado automáticamente)"
    )
    
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unidad de Medida",
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    )
    
    # NUEVO: Campo de texto para nombre del embalaje
    packaging_name = fields.Char(
        string="Nombre del Embalaje",
        help="Escribe el nombre del embalaje y se creará automáticamente al guardar"
    )
    
    # -------------------------------------------------------------------------
    # CORRECCIÓN ODOO 19:
    # product.packaging fue eliminado. Usamos uom.uom que ahora gestiona los empaques.
    # -------------------------------------------------------------------------
    packaging_id = fields.Many2one(
        'uom.uom', 
        string="Embalaje Creado",
        readonly=True,
        help="Embalaje creado automáticamente (UoM tipo Empaque)"
    )
    
    # Servicio asociado (solo lectura)
    product_id = fields.Many2one(
        'product.product', 
        string="Servicio Asociado",
        readonly=True,
        help="Producto/servicio creado o asociado a partir de este residuo"
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
                record.weight_per_unit = record.weight_kg / record.volume
    
    @api.onchange('create_new_service')
    def _onchange_create_new_service(self):
        """Limpiar campos según la opción seleccionada"""
        if self.create_new_service:
            self.existing_service_id = False
            self.product_id = False
            if not self.uom_id:
                self.uom_id = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        else:
            if not self.existing_service_id:
                self.product_id = False

    @api.onchange('existing_service_id')
    def _onchange_existing_service_id(self):
        """Cuando selecciona un servicio existente, cargar su información"""
        if self.existing_service_id and not self.create_new_service:
            service = self.existing_service_id
            
            self.product_id = service.id
            self.name = service.name
            self.uom_id = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            
            # -----------------------------------------------------------------
            # CORRECCIÓN ODOO 19: Buscamos en uom.uom en lugar de product.packaging
            # -----------------------------------------------------------------
            packagings = self.env['uom.uom'].search([
                ('product_id', '=', service.id)
            ])
            
            if packagings:
                self.packaging_id = packagings[0].id
                self.packaging_name = packagings[0].name
            
            # Intentar extraer información de la descripción
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
    
    @api.constrains('create_new_service', 'name', 'existing_service_id')
    def _check_required_fields(self):
        """Validar campos requeridos según el modo"""
        for record in self:
            if record.create_new_service:
                if not record.name:
                    raise ValidationError("El nombre del residuo es obligatorio cuando se crea un nuevo servicio.")
            else:
                if not record.existing_service_id:
                    raise ValidationError("Debe seleccionar un servicio existente o marcar '¿Es Nuevo?' para crear uno.")
    
    def _create_or_update_packaging_v19(self, record):
        """Helper para crear/actualizar empaque (ahora UoM) en Odoo 19"""
        if record.packaging_name and record.product_id and not record.packaging_id:
            try:
                # En Odoo 19, creamos un UoM específico linkeado al producto
                # Debemos asegurar que el UoM tenga la misma categoría que la unidad base del producto
                category = record.product_id.uom_id.category_id
                
                if category:
                    packaging_uom = self.env['uom.uom'].create({
                        'name': record.packaging_name,
                        'category_id': category.id,
                        'uom_type': 'bigger', # Empaque suele ser mayor que la unidad
                        'ratio': record.volume or 1.0, # ratio reemplaza a factor en esta lógica
                        'product_id': record.product_id.id,
                        'active': True,
                    })
                    record.packaging_id = packaging_uom.id
            except Exception as e:
                _logger.warning(f"Error al crear embalaje (UoM) en Odoo 19: {str(e)}")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Crear servicio y embalaje si es necesario
        """
        uom_unit = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        for vals in vals_list:
            if not vals.get('uom_id') and uom_unit:
                vals['uom_id'] = uom_unit.id
        
        records = super().create(vals_list)
        
        for record in records:
            # PASO 1: Crear o asignar producto
            if not record.create_new_service and record.existing_service_id:
                record.product_id = record.existing_service_id.id
                
            elif record.create_new_service and record.name and record.plan_manejo and record.residue_type:
                try:
                    service = record.lead_id._create_service_from_residue(record)
                    record.product_id = service.id
                except Exception as e:
                    _logger.warning(f"Error al crear servicio: {str(e)}")
            
            # PASO 2: Crear embalaje (Adaptado a Odoo 19)
            self._create_or_update_packaging_v19(record)
        
        return records
    
    def write(self, vals):
        """
        Actualizar servicio y crear embalaje si es necesario
        """
        result = super().write(vals)
        
        for record in self:
            # PASO 1: Actualizar o crear producto
            if 'existing_service_id' in vals and not record.create_new_service and record.existing_service_id:
                record.product_id = record.existing_service_id.id
            
            elif record.create_new_service:
                if not record.product_id and record.name and record.plan_manejo and record.residue_type:
                    try:
                        service = record.lead_id._create_service_from_residue(record)
                        record.product_id = service.id
                    except Exception as e:
                        _logger.warning(f"Error al crear servicio: {str(e)}")
                
                elif record.product_id and record.name:
                    try:
                        record.product_id.write({
                            'name': record.name,
                            'description_sale': f"""Servicio de manejo de residuo: {record.name}
Plan de manejo: {dict(record._fields['plan_manejo'].selection).get(record.plan_manejo, '') if record.plan_manejo else 'No especificado'}
Tipo de residuo: {dict(record._fields['residue_type'].selection).get(record.residue_type, '') if record.residue_type else 'No especificado'}
Capacidad: {record.capacity} L
Peso estimado: {record.weight_kg} kg
Unidades: {record.volume} {record.uom_id.name if record.uom_id else ''}""",
                        })
                    except Exception as e:
                        _logger.warning(f"Error al actualizar servicio: {str(e)}")
            
            # PASO 2: Crear embalaje (Adaptado a Odoo 19)
            if 'packaging_name' in vals:
                 self._create_or_update_packaging_v19(record)
        
        return result```

## ./views/crm_lead_view.xml
```xml
<odoo>
  <record id="view_crm_lead_form_custom" model="ir.ui.view">
    <field name="name">crm.lead.form.custom</field>
    <field name="model">crm.lead</field>
    <field name="inherit_id" ref="crm.crm_lead_view_form"/>
    <field name="arch" type="xml">

      <xpath expr="//notebook" position="inside">

        <!-- Página de Validación de Residuos -->
        <page string="Validación de Residuos" name="residue_validation">
          <group string="Validación de Residuo Nuevo">
            <field name="residue_new"/>
            <div invisible="not show_sample_alert" style="margin: 10px 0;">
              <div class="alert alert-warning" role="alert">
                <i class="fa fa-warning"/>
                <strong>Atención:</strong> Se requiere solicitar muestra al cliente para análisis.
              </div>
            </div>
            <field name="sample_result_file" filename="sample_result_filename" widget="pdf_viewer" invisible="not residue_new" options="{'force_save': True}"/>
            <field name="sample_result_filename" invisible="1"/>
          </group>

          <group string="Validación de Visita Presencial">
            <field name="requiere_visita"/>
            <div invisible="not show_visita_alert" style="margin: 10px 0;">
              <div class="alert alert-warning" role="alert">
                <i class="fa fa-warning"/>
                <strong>Atención:</strong> Se requiere validar residuos y volúmenes en sitio y subir el informe correspondiente.
              </div>
            </div>
            <field name="visita_validation_file" filename="visita_validation_filename" widget="pdf_viewer" invisible="not requiere_visita" options="{'force_save': True}"/>
            <field name="visita_validation_filename" invisible="1"/>
          </group>

          <field name="show_sample_alert" invisible="1"/>
          <field name="show_visita_alert" invisible="1"/>
        </page>

        <!-- Página de Servicios - UNA SOLA LISTA -->
        <page string="Gestión de Servicio" name="residuos">
          <separator string="Listado de Servicios y Residuos"/>
          
          <group>
            <field name="residue_line_ids" nolabel="1">
              <list editable="bottom">
                <!-- Checkbox para identificar si es nuevo -->
                <field name="create_new_service" string="¿Nuevo?"/>
                
                <!-- Campo para seleccionar servicio existente (visible cuando NO es nuevo) -->
                <field name="existing_service_id"
                       string="Servicio Existente"
                       domain="[('sale_ok','=',True), ('type','=','service')]"
                       options="{'no_create': True}"
                       optional="show"/>
                
                <!-- Campos SIEMPRE EDITABLES -->
                <field name="name" string="Nombre"/>
                <field name="residue_type" string="Tipo"/>
                <field name="plan_manejo" string="Plan de Manejo"/>
                <field name="capacity" string="Capacidad"/>
                <field name="weight_kg" string="Peso (kg)"/>
                <field name="volume" string="Unidades"/>
                <field name="weight_per_unit" string="Kg/Unidad" readonly="1"/>
                <field name="uom_id" string="UoM"/>
                
                <!-- NUEVO: Campo de texto para nombre del embalaje -->
                <field name="packaging_name" string="Nombre Embalaje"/>
                
                <!-- Embalaje creado (solo lectura) -->
                <field name="packaging_id" string="Embalaje" readonly="1" optional="show"/>
                
                <!-- Servicio asociado (solo lectura) -->
                <field name="product_id" string="Servicio" readonly="1" optional="show"/>
                
                <button name="%(product.product_template_action)d"
                        type="action"
                        icon="fa-external-link"
                        title="Ver servicio"
                        context="{'search_default_id': product_id}"
                        invisible="not product_id"/>
              </list>

              <form>
                <group>
                  <group string="Tipo de Servicio">
                    <field name="create_new_service"/>
                    
                    <!-- Selección de servicio existente -->
                    <field name="existing_service_id"
                           string="Servicio Existente"
                           domain="[('sale_ok','=',True), ('type','=','service')]"
                           options="{'no_create': True}"
                           placeholder="Buscar servicio existente..."
                           invisible="create_new_service"
                           required="not create_new_service"/>
                  </group>
                  
                  <group string="Información del Servicio/Residuo">
                    <field name="name" required="1"/>
                    <field name="residue_type"/>
                    <field name="plan_manejo"/>
                    <field name="product_id" readonly="1"/>
                  </group>
                </group>
                
                <group string="Cantidades, Capacidad y Peso">
                  <group>
                    <field name="capacity"/>
                    <field name="weight_kg"/>
                    <field name="volume"/>
                    <field name="weight_per_unit" readonly="1"/>
                  </group>
                  <group>
                    <field name="uom_id"/>
                  </group>
                </group>
                
                <group string="Embalaje">
                  <group>
                    <field name="packaging_name" 
                           placeholder="Escribe el nombre del embalaje (ej: Tambor 200L, Contenedor IBC, Bolsa 50kg)"
                           help="Escribe el nombre y se creará automáticamente al guardar"/>
                    <field name="packaging_id" readonly="1"/>
                  </group>
                </group>
              </form>
            </field>
          </group>
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

        <!-- Página de Información del Prospecto -->
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
            </group>
            <group>
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
</odoo>```

