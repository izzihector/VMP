from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from odoo.osv import osv
from odoo.addons import decimal_precision as dp
from odoo.http import request
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        res = super(purchase_order, self).button_confirm()
        if res:
            for order in self:
                for line in order.order_line:
                    line.product_id.write({'standard_price': line.cost_price})
                    att_values = line.product_id.attribute_value_ids.mapped('id')
                    template_attributes = self.env['product.template.attribute.value'].search([
                        ('product_attribute_value_id', 'in', att_values)])
                    template_attributes.write({'cost_price': line.cost_price})
        return res
  
    
class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'
    
    rendimiento = fields.Float('Rendimiento', digits=(12, 3), store=True)
    qty_custom = fields.Float('Cantidad x Unidad', store=True, default=1.0)
    product_qty = fields.Float(string='Rendimiento', digits=dp.get_precision('Product Unit of Measure'), required=True, invisible=True)
    cost_price = fields.Float('Precio Costo', default=0.0, digits=(16, 4), help="Costo por compra.")
    price_unit = fields.Float(digits=(16, 4))

    _columns = {
                    'rendimiento': fields.Float('Rendimiento'),
                    'qty_custom': fields.Float('Cantidad x Unidad'),
                    'product_qty': fields.Float('Rendimiento', invisible=True),
                    'cost_price': fields.Float('Precio Costo'),

               }
    _defaults = {
        'rendimiento': 0.0,
        'qty_custom': 1.0,
        'product_qty': 1.0,
        'cost_price': 0.0
    }

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(purchase_order_line, self).onchange_product_id()
        att_values = self.product_id.attribute_value_ids.mapped('id')
        template_attributes = self.env['product.template.attribute.value'].search([
            ('product_attribute_value_id', 'in', att_values)])
        if template_attributes:
            self.cost_price = template_attributes[0].cost_price
        else:
            self.cost_price = 0.0
        return result


    @api.onchange('cost_price','product_id', 'price_unit', 'product_uom', 'product_qty', 'tax_id', 'qty_custom')
    def update_after_product_id(self):
        if(self.product_id.id): 
            product_template =  self.env['product.template'].search([('id','=',self.product_id.product_tmpl_id.id)])

            query = "select product_attribute_value_id from product_attribute_value_product_product_rel where product_product_id = "+str(self.product_id.id)
            request.cr.execute(query)
            product_attribute_value_product_product_rel = request.cr.dictfetchone()

            if(product_attribute_value_product_product_rel):
                product_template_variant_values =  self.env['product.template.attribute.value'].search([('product_attribute_value_id','=', product_attribute_value_product_product_rel['product_attribute_value_id'])])
                for product_variant in product_template_variant_values:
                    variant_puom = product_variant.variant_puom
                    
                    if(variant_puom):
                        
                        variant_puom = variant_puom.split('-')
                        variant_puom_id = variant_puom[0]

                        cost_price = product_variant.cost_price if self.cost_price <= 0.0 else self.cost_price

                        self.rendimiento = float(product_variant.variant_ratio) * float(self.qty_custom)
                        self.product_qty = self.rendimiento
                        self.price_unit =  (float(cost_price) / float(self.rendimiento)) * float(self.qty_custom)
                        # self.cost_price = product_variant.cost_price

                        if not (self.product_id and self.product_uom and

                            self.env.user.has_group('sale.group_discount_per_so_line')):
                            return
            #else:
            #    raise Warning("isa")
            
    @api.onchange( 'product_qty')
    def update_product_qty(self):
         if(self.product_id.id): 
            query = "select product_attribute_value_id from product_attribute_value_product_product_rel where product_product_id = "+str(self.product_id.id)
            request.cr.execute(query)
            product_attribute_value_product_product_rel = request.cr.dictfetchone()

            if(product_attribute_value_product_product_rel):
                pass
            else:
                self.qty_custom = self.product_qty
    
    @api.onchange( 'qty_custom')
    def update_qty_custom(self):
         if(self.product_id.id): 
            query = "select product_attribute_value_id from product_attribute_value_product_product_rel where product_product_id = "+str(self.product_id.id)
            request.cr.execute(query)
            product_attribute_value_product_product_rel = request.cr.dictfetchone()

            if(product_attribute_value_product_product_rel):
                pass
            else:
                self.product_qty = self.qty_custom
        

    def _get_factor_inv(self, unit_id):
        uom =  self.env['uom.uom'].search([('active','=',True),('id','=',unit_id)],limit=1)
        return uom.factor_inv

    def _get_uom_reference(self,any_uom_id):              
        uom =  self.env['uom.uom'].search([('id','=',any_uom_id)],limit=1)
        uom_reference =  self.env['uom.uom'].search([('active','=',True),('category_id','=',uom.category_id.id), ('uom_type','=','reference')],limit=1)
        return uom_reference

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(purchase_order_line, self)._prepare_stock_moves(picking)
        if res:
            res[0]['product_uom_qty_purchase'] = self.qty_custom
        return res