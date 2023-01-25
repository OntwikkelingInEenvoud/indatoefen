from odoo import models, fields, api, exceptions


class ObjectTools(models.Model):
    _name = 'oi1.object_tools'
    _description = "object tools"

    @api.model
    def get_dictionary_values(self, list_object):
        list_object_dict_vals = []
        for object in list_object:
            list_object_dict_vals.append(self._get_object_vals(object))
        return list_object_dict_vals

    @staticmethod
    def get_id_list(values):
        key_list = []
        for value in values:
            for key in value:
                if key == 6:
                    key_list += value[2]
                if key == 4:
                    key_list += value[1]
        return key_list

    @api.model
    def _get_object_vals(self, odoo_object):
        def get_prop(prop_item):
            props = odoo_object.fields_get(key).items()
            for k, v in props:
                if k == key:
                    return v[prop_item]
            return False

        def get_to_store():
            return get_prop('store')

        def get_odoo_api_value(object_value):
            prop_type = get_prop('type')
            if prop_type in ('many2one'):
                return object_value.id
            else:
                ids = []
                for record in object_value:
                    if record.id:
                        ids.append(record.id)
                if ids and len(ids) > 0:
                    return [(6, 0, ids)]
            return False

        vals = {}
        for key in odoo_object.fields_get():
            if key in ('id', 'write_uid', 'write_date', 'create_uid', 'create_date'):
                continue
            value = odoo_object[key]
            str_type = str(type(value))
            if get_to_store():
                if 'odoo.api' in str_type:
                    value = get_odoo_api_value(value)
            vals[key] = value
        return vals
