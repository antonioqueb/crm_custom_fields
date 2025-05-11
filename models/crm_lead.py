from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    service_frequency = fields.Char(string="Frecuencia del Servicio")
    residue_line_ids = fields.One2many('crm.lead.residue', 'lead_id', string="Listado de Residuos")
    residue_new = fields.Boolean(string="¿Residuo Nuevo?")
    show_sample_alert = fields.Boolean(string="Mostrar alerta de muestra", compute="_compute_show_sample_alert")

    def _compute_show_sample_alert(self):
        for lead in self:
            lead.show_sample_alert = lead.residue_new

class CrmLeadResidue(models.Model):
    _name = 'crm.lead.residue'
    _description = 'Residuo cotizado'

    lead_id = fields.Many2one('crm.lead', string="Lead/Oportunidad", required=True, ondelete='cascade')
    name = fields.Char(string="Residuo", required=True)
    volume = fields.Float(string="Volumen", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unidad de Medida", required=True)
