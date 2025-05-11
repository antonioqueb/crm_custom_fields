from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    service_frequency = fields.Char(string="Frecuencia del Servicio")
    residue_line_ids = fields.One2many('crm.lead.residue', 'lead_id', string="Listado de Residuos")
    residue_new = fields.Boolean(string="¿Residuo Nuevo?")
    show_sample_alert = fields.Boolean(
        string="Mostrar alerta de muestra",
        compute="_compute_show_sample_alert"
    )
    sample_result_ids = fields.One2many(
        'crm.lead.sample.result',
        'lead_id',
        string="Resultados de Muestras"
    )

    @api.depends('residue_new')
    def _compute_show_sample_alert(self):
        for lead in self:
            lead.show_sample_alert = lead.residue_new

class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

    lead_id = fields.Many2one('crm.lead', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    volume = fields.Float(required=True)
    uom_id = fields.Many2one('uom.uom', required=True)

class CrmLeadSampleResult(models.Model):
    _name = 'crm.lead.sample.result'
    _description = 'Resultado de Muestra'

    lead_id = fields.Many2one('crm.lead', required=True, ondelete='cascade')
    name = fields.Char(string="Descripción del archivo", required=True)
    file = fields.Binary(string="Archivo", required=True)
    filename = fields.Char(string="Nombre del Archivo")
    upload_date = fields.Datetime(
        string="Fecha de Subida",
        default=fields.Datetime.now
    )
