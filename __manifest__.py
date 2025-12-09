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