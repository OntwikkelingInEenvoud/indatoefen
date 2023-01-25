from odoo import models, api
from odoo import exceptions
from odoo import _


class OdooImport(models.TransientModel):
    _name = 'oi1_odooimport'
    _description = 'Odoo excel import'

    def do_import_res_partner_records(self, records):
        res_partner_obj = self.env['res.partner']
        table_conversion_obj = self.env['oi1_dataimport.table_conversion']

        for record in records:
            print(record)
            debtorno = str("")
            prev_code = False
            res_partner = False
            parent = False

            if 'prev_code' in record:
                prev_code = record['prev_code']
                tables = table_conversion_obj.search([('prev_code', '=', prev_code),
                                                       ('res_model_name', '=', 'res.partner')
                                                       ])
                if len(tables) > 0:
                    res_partner = res_partner_obj.browse([tables.res_id])[0]

            if 'debtorno' in record and not prev_code:
                debtorno = record['debtorno']
                res_partners = res_partner_obj.search([('x_prev_code', '=', debtorno), ])
                if len(res_partners) > 0:
                    res_partner = res_partners[0]
            name = record['name'].strip()

            if 'debtorno' not in record and name != "":
                res_partners = res_partner_obj.search([('name', '=', name), ]);
                if len(res_partners) == 1:
                    res_partner = res_partners[0];
                if len(res_partners) > 1:
                    res_partners = res_partner_obj.search([('name', '=', name), ('is_company', '=', True)]);
                    if len(res_partners) == 1:
                        res_partner = res_partners[0]
                    if len(res_partners) != 1:
                        continue;

            if 'x_parent_prev_code' in record:
                x_parent_prev_code = record['x_parent_prev_code']
                tables = table_conversion_obj.search([('prev_code', '=',  x_parent_prev_code),
                                                      ('res_model_name', '=', 'res.partner')
                                                      ])
                if len(tables) > 0:
                    parent = res_partner_obj.browse([tables.res_id])[0]

            if 'x_parent_name' in record:
                x_parent_name = record['x_parent_name']
                parents = res_partner_obj.search([('name', '=', x_parent_name)])
                if len(parents) == 1:
                    parent = parents[0]

            if name == "":
                continue

            if parent:
                contacts = res_partner_obj.search([('parent_id', '=', parent.id),
                                                   ('name', '=', name)])
                if len(contacts) > 0:
                    res_partner = contacts[0]

            if not res_partner and 'ref' in record:
                ref = record['ref'].strip()
                if len(ref) > 0:
                    res_partners = res_partner_obj.search([('ref','=', ref)])
                    if len(res_partners) == 1:
                        res_partner = res_partners[0]

            if not res_partner:
                is_company = False
                if 'iscompany' in record:
                    is_company = self._returnBooleanValueFromString(record['iscompany']);
                res_partner = res_partner_obj.create({'name': name, 'is_company': is_company});

            values = {}
            if parent and parent.id != res_partner.id:
                values['parent_id'] = parent
            values['name'] = name
            if debtorno != "":
                values['x_prev_code'] = debtorno;
            if 'x_mnem' in record:
                values['x_mnem'] = record['x_mnem']
            if 'x_name' in self.env['res.partner']._fields:
                values['x_name'] = name;
            if 'x_firstname' in record and 'x_first_name' in self.env['res.partner']._fields:
                values['x_first_name'] = record['x_firstname']
            if 'street' in record:
                values['street'] = record['street'];
            if 'street2' in record:
                values['street2'] = record['street2']
            if 'street_number' in record:
                values['street_number'] = record['street_number']
                if 'street_name' not in record and 'street' in record:
                    values['street_name'] = values['street']
                if 'street_number2' not in record:
                    values['street_number2'] = ''
            if 'lang' in record:
                lang = record['lang']
                chosen_language = False
                language_obj = self.env['res.lang']
                languages = language_obj.search([('iso_code', '=', lang)])
                if len(languages) == 1:
                    chosen_language = languages[0].code
                if not chosen_language:
                    for language in language_obj.search([]):
                        language_names = language.name.split('/')
                        for language_name in language_names:
                            if language_name.lower().strip() == lang.lower().strip():
                                chosen_language = language.code
                if chosen_language:
                    values['lang'] = chosen_language
                if not chosen_language:
                    raise exceptions.UserError(_("No language found with the iso_code or name %s") % lang)

            if 'countryname' in record:
                countryCode = ''
                countryName = record['countryname'].strip()
                if countryName == 'Nederland':
                    countryCode = 'NL'
                if countryCode == '' and countryName != '':
                    Countries = self.env['res.country'].search([('name', '=', countryName)])
                    if len(Countries) == 0:
                        Countries = self.env['res.country'].with_context(lang='en_US').search(
                            [('name', '=', countryName)])
                    if len(Countries) > 0:
                        res_partner.country_id = Countries[0];
                if countryCode != '':
                    Countries = self.env['res.country'].search([('code', '=', countryCode)]);
                    if len(Countries) > 0:
                        values['country_id'] = Countries[0].id

            if 'x_coc' in record:
                values['x_coc'] = record['x_coc']
            if 'countrycode' in record:
                countryCode = record['countrycode'].strip()
                if countryCode == "B":
                    countryCode = "BE"
                if countryCode == "D":
                    countryCode = "DE"
                Countries = self.env['res.country'].search([('code', '=', countryCode)]);
                if len(Countries) > 0:
                    values['country_id'] = Countries[0].id;
            if 'zip' in record:
                values['zip'] = record['zip']
            if 'city' in record:
                values['city'] = record['city']
            if 'phone' in record:
                values['phone'] = record['phone']
            if 'fax' in record:
                values['fax'] = record['fax'];
            if 'iscompany' in record:
                values['is_company'] = self._returnBooleanValueFromString(record['iscompany']);
            if 'comment' in record:
                values['comment'] = record['comment']
            if 'function' in record:
                values['function'] = record['function']
            if 'x_gender' in record:
                gender = record['x_gender'].lower()
                if gender in ('mr.', 'heer'):
                    gender = 'm'
                if gender in ('mrs.', 'mevrouw', 'miss'):
                    gender = 'f'
                try:
                    res_partner.x_gender = gender
                except Exception as e:
                    print(e)
                    pass
            if 'x_name' in record and 'x_name' in self.env['res.partner']._fields:
                if record['x_name'] != '':
                    values['x_name'] = record['x_name']
            if 'x_initials' in record:
                values['x_initials'] = record['x_initials']

            if 'vat' in record:
                vat = record['vat'].strip()
                vat = vat.replace(" ", "")
                vat = vat.replace(".", "")
                vat = vat.replace("-", "")
                if len(vat) > 2:
                    landcode = vat[0:2]
                    if not res_partner.country_id.id:
                        Countries = self.env['res.country'].search([('code', '=', landcode)])
                        if len(Countries) > 0:
                            res_partner.country_id = Countries[0]
                            print("Country set to " + res_partner.country_id.name + "from vat " + vat)
                    if res_partner.country_id.id:
                        try:
                            res_partner.vat = vat
                        # res_partner.check_vat()
                        except Exception as e:
                            print(e)
                            res_partner.vat = ''
                            pass
            if 'email' in record:
                email = record['email']
                if '@' in email:
                    values['email'] = email
            if 'website' in record:
                values['website'] = record['website']
            if 'ref' in record:
                values['ref'] = record['ref']
            if 'mobile' in record:
                values['mobile'] = record['mobile']
            if len(values) > 0:
                res_partner.write(values)
                if 'x_first_name' in values or 'x_name' in values or 'x_initials' in values:
                    res_partner.adjust_name()
            self.env.cr.commit()
            if 'property_supplier_payment_term_description' in record:
                self.set_vendor_payment_term(res_partner, record['property_supplier_payment_term_description'])

            parent_id = res_partner.id
            if 'deliverystreet' in record:
                res_partner.is_company = True
                street = record['deliverystreet']
                if street.strip() != '':
                    del_partner = False
                    res_partners = res_partner_obj.search([('parent_id', '=', parent_id),
                                                           ('type', '=', 'delivery'),
                                                           ('street', '=', street)
                                                              , ]);
                    if len(res_partners) > 0:
                        del_partner = res_partners[0]
                    if del_partner == False:
                        del_partner = res_partner_obj.create(
                            {'parent_id': parent_id, 'type': 'delivery', 'street': street});
                    if 'deliveryname' in record:
                        del_partner.name = record['deliveryname']
                    if 'deliveryname' not in record:
                        del_partner.name = name
                    if 'deliverycity' in record:
                        del_partner.city = record['deliverycity']
                    if 'deliveryzip' in record:
                        del_partner.zip = record['deliveryzip']
                    self.env.cr.commit();
            if 'iban' in record:
                iban = record['iban'].strip()
                if iban != '':
                    Bank_Obj = self.env['res.partner.bank']
                    Bank = False
                    Banks = Bank_Obj.search([('acc_number', '=', iban)])
                    if len(Banks) > 0:
                        Bank = Banks[0]
                    if Bank == False:
                        Bank = Bank_Obj.create({'acc_number': iban, 'partner_id': parent_id})
                    Bank.partner_id = parent_id
                    Bank.acc_holder_name = name
                    self.env.cr.commit();

            if prev_code:
                self.set_table_conversion(prev_code, 'res.partner', '' ,res_partner.id)


    def set_vendor_payment_term(self, partner, payment_term_desc):
        if len(payment_term_desc) == 0:
            return
        payment_term_obj = self.env['account.payment.term']
        property_obj = self.env['ir.property']
        model_fields_obj = self.env['ir.model.fields']

        model_fields = model_fields_obj.search([('model', '=', 'res.partner'),
                                               ('name', '=', 'property_supplier_payment_term_id')
                                               ])
        fields_id = False
        if len(model_fields) > 0:
            fields_id = model_fields[0].id

        payment_terms = payment_term_obj.search([('name','=', payment_term_desc)])
        if len(payment_terms) == 0:
            raise exceptions.UserError(_("Payment term with description %s not found") % payment_term_desc)
        payment_term = payment_terms[0]
        name = 'property_supplier_payment_term_id'
        res_id = 'res.partner,' + str(partner.id)
        value_reference = 'account.payment.term,' + str(payment_term.id)
        property = False
        properties = property_obj.search([('name', '=', name),
                                          ('res_id', '=', res_id)])
        if len(properties) > 0:
           property = properties[0]
        if not property:
           property_obj.create({'name': name,'res_id':res_id, 'value_reference': value_reference, 'fields_id': fields_id})
        if property:
           property.write({'value_reference': value_reference})





    def _returnBooleanValueFromString(self, value):
        boolValue = False;
        if value == "1" or value == "Waar" or value == "True" or value == "YES":
            boolValue = True;
        return boolValue;

    def do_import_account_records(self, records):
        Account_Obj = self.env['account.account'];
        AccountType_Obj = self.env['account.account.type'];

        default_accounttype_id = self.do_get_id_from_translation('account.account.type,name', 'Afschrijving');
        if default_accounttype_id == 0:
            raise exceptions.UserError(_("Er kon geen default type voor de grootboekrekening worden bepaald"));

        for record in records:
            name = ""
            code = ""
            AccountType = False
            Account = False
            print(record)

            if 'name' in record:
                name = record['name'];
            if 'code' in record:
                code = record['code'];
            if code != "":
                Accounts = Account_Obj.search([('code', '=', code), ]);
                if len(Accounts) > 0:
                    Account = Accounts[0];
            if name != "" and Account == False:
                Accounts = Account_Obj.search([('name', '=', name), ]);
                if len(Accounts) > 0:
                    Account = Accounts[0];

            if Account == False:
                Account = Account_Obj.create({'name': name,
                                              'code': code,
                                              'user_type_id': default_accounttype_id,
                                              });

            if 'usertype_id' in record:
                usertype_id = record['usertype_id']
                AccountTypes = AccountType_Obj.search([('name', '=', usertype_id)]);
                if len(AccountTypes) > 0:
                    AccountType = AccountTypes[0];
                if AccountType == False:
                    id = self.do_get_id_from_translation('account.account.type,name', usertype_id);
                    if id != 0:
                        AccountType = AccountType_Obj.browse([id])[0];
                if AccountType == FalFse:
                    raise exceptions.UserError(_("Er kon geen grootbookrekening type %s worden gevonden.") % usertype_id)

            values = {}
            if 'reconcile' in record:
                reconcile = record['reconcile']
                reconcile = self.do_get_boolean_from_excel(reconcile)
                values['reconcile'] = reconcile
            if AccountType:
                values['user_type_id'] = AccountType.id
            if name:
                values['name'] = name
            if code:
                values['code'] = code
            Account.write(values)
         

    @staticmethod
    def do_get_boolean_from_excel(value):
        if not value:
            return value
        value = str(value).strip()
        if value == '1' or value.lower() == 'x' or value.lower() == 'true' or value.lower() == 'waar':
            return True
        return False

    def do_get_id_from_translation(self, field, value):
        translation_obj = self.env['ir.translation']
        translations = translation_obj.search([('name', '=', field),
                                               ('value', '=', value),
                                               ])

        if len(translations) > 0:
            return translations[0].res_id
        return 0

    @api.model
    def set_table_conversion(self, prev_code, object, info, res_id):
        table_conversion_obj = self.env['oi1_dataimport.table_conversion']
        tables = table_conversion_obj.search([('prev_code', '=', prev_code),
                                              ('res_model_name', '=',  object),
                                              ('res_id', '=', res_id)])
        if len(tables) == 0:
            table_conversion_obj.sudo().create({'prev_code': prev_code,
                                         'res_model_name': object,
                                         'res_id': res_id})


