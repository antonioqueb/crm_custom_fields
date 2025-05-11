-e ### models/__init__.py
```
from . import crm_lead
```

-e ### models/crm_lead.py
```
from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    service_frequency = fields.Char(string="Frecuencia del Servicio")
    residue_line_ids = fields.One2many('crm.lead.residue', 'lead_id', string="Listado de Residuos")
    residue_new = fields.Boolean(string="¿Residuo Nuevo?")
    show_sample_alert = fields.Boolean(string="Mostrar alerta de muestra", compute="_compute_show_sample_alert")
    sample_result_file = fields.Binary(string="Archivo de Resultados de Muestra")
    sample_result_filename = fields.Char(string="Nombre del Archivo de Resultados de Muestra")
    requiere_visita = fields.Boolean(string="Requiere visita presencial")


    @api.depends('residue_new')
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
```

-e ### views/crm_lead_view.xml
```
<!-- views/crm_lead_view.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <record id="view_crm_lead_form_custom_fields" model="ir.ui.view">
        <field name="name">crm.lead.form.custom.fields</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_lead_view_form"/>
        <field name="arch" type="xml">
            <xpath expr="//page[@name='extra']" position="after">
                <page string="Información del Servicio" name="service_info">
                    <group>
                        <field name="requiere_visita"/>
                        <field name="service_frequency"/>
                        <field name="residue_new"/>
                        <div invisible="not show_sample_alert">
                            <p style="color:#d9534f; font-weight:bold;">
                                ⚠️ Solicitar muestra al cliente.
                            </p>
                            <field name="sample_result_file" filename="sample_result_filename" widget="pdf_viewer"/>
                        </div>
                    </group>
                    <group>
                        <field name="residue_line_ids">
                            <list editable="bottom">
                                <field name="name"/>
                                <field name="volume"/>
                                <field name="uom_id" options="{'no_create': True}"/>
                            </list>
                        </field>
                    </group>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

### __init__.py
```
from . import models
```
### __manifest__.py
```
{
    'name': 'CRM Custom Fields',
    'version': '18.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'Añade campos personalizados en oportunidades CRM.',
    'author': 'Alphaqueb Consulting',
    'depends': ['crm', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```
