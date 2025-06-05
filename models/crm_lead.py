# models/crm_lead.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    service_frequency = fields.Char(string="Frecuencia del Servicio")
    residue_line_ids = fields.One2many('crm.lead.residue', 'lead_id', string="Listado de Residuos")
    
    residue_new = fields.Boolean(string="¿Residuo Nuevo?")
    show_sample_alert = fields.Boolean(
        string="Mostrar alerta de muestra",
        compute="_compute_show_sample_alert",
        store=True
    )
    sample_result_file = fields.Binary(string="Archivo de Resultados de Muestra")
    sample_result_filename = fields.Char(string="Nombre del Archivo de Resultados de Muestra")
    
    requiere_visita = fields.Boolean(string="Requiere visita presencial")
    show_visita_alert = fields.Boolean(
        string="Mostrar alerta visita",
        compute="_compute_show_visita_alert",
        store=True
    )
    visita_validation_file = fields.Binary(string="Archivo de validación de visita")
    visita_validation_filename = fields.Char(string="Nombre del archivo de validación de visita")

    pickup_location = fields.Char(
        string="Ubicación de recolección",
        help="Dirección exacta (planta, almacén, muelle, etc.) donde se retira el residuo."
    )

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
        service_name = f"Servicio de {residue.name} - {dict(residue._fields['plan_manejo'].selection).get(residue.plan_manejo, '')}"
        
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
    
    @api.model_create_multi
    def create(self, vals_list):
        """Crear servicios automáticamente al crear residuos"""
        records = super().create(vals_list)
        for record in records:
            if record.name and record.plan_manejo and not record.product_id:
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
            # Si se modifican campos importantes y no hay servicio, crear uno
            if ('name' in vals or 'plan_manejo' in vals) and not record.product_id:
                if record.name and record.plan_manejo:
                    try:
                        service = record.lead_id._create_service_from_residue(record)
                        record.product_id = service.id
                    except Exception:
                        pass
            # Si ya existe servicio, actualizar su nombre
            elif record.product_id and ('name' in vals or 'plan_manejo' in vals):
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