class StockMovementCustomHandler(models.AbstractModel):
    _name = 'account.stock.movement.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Stock Movement Custom Handler'


    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals,warnings=None):
        if self.env.context.get('print_mode') and options.get('filter_search_bar'):
            # Handled here instead of in custom options initializer as init_options functions aren't re-called when printing the report.
            options.setdefault('forced_domain', []).append(
                ('product_id.display_name', 'ilike', options['filter_search_bar']))

        partner_lines, totals_by_column_group = self._build_partner_lines(report, options)

        lines = report._regroup_lines_by_name_prefix(options, partner_lines,
                                                     '_report_expand_unfoldable_line_partner_ledger_prefix_group', 0)
        lines = [(0, line) for line in lines]

        # Report total line.
        lines.append((0, self._get_report_line_total(options, totals_by_column_group)))

        return lines

    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: {
                total: 0.0
                for total in
                ['open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance', 'end_balance_amount',
                 'main_uom_qty', 'unit_cost', 'debit', 'credit',
                 'balance']
            }
            for column_group_key in options['column_groups']
        }

        for partner, results in self._query_partners(options):
            partner_values = defaultdict(dict)
            for column_group_key in options['column_groups']:
                partner_sum = results.get(column_group_key, {})

                partner_values[column_group_key]['main_uom_qty'] = partner_sum.get('main_uom_qty', 0.0)
                partner_values[column_group_key]['unit_cost'] = partner_sum.get('unit_cost', 0.0)
                partner_values[column_group_key]['open_balance'] = partner_sum.get('open_balance', 0.0)
                partner_values[column_group_key]['open_balance_amount'] = partner_sum.get('open_balance_amount', 0.0)
                partner_values[column_group_key]['stock_in'] = partner_sum.get('stock_in', 0.0)
                partner_values[column_group_key]['stock_out'] = partner_sum.get('stock_out', 0.0)
                partner_values[column_group_key]['end_balance'] = partner_sum.get('end_balance', 0.0)
                partner_values[column_group_key]['end_balance_amount'] = partner_sum.get('end_balance_amount', 0.0)
                partner_values[column_group_key]['debit'] = partner_sum.get('debit', 0.0)
                partner_values[column_group_key]['credit'] = partner_sum.get('credit', 0.0)
                partner_values[column_group_key]['balance'] = partner_sum.get('balance', 0.0)

                totals_by_column_group[column_group_key]['main_uom_qty'] += partner_values[column_group_key][
                    'main_uom_qty']
                totals_by_column_group[column_group_key]['unit_cost'] = partner_values[column_group_key]['unit_cost']
                totals_by_column_group[column_group_key]['open_balance'] = partner_values[column_group_key][
                    'open_balance']
                totals_by_column_group[column_group_key]['open_balance_amount'] = partner_values[column_group_key][
                    'open_balance_amount']
                totals_by_column_group[column_group_key]['stock_in'] = partner_values[column_group_key]['stock_in']
                totals_by_column_group[column_group_key]['stock_out'] = partner_values[column_group_key]['stock_out']
                totals_by_column_group[column_group_key]['end_balance'] = partner_values[column_group_key][
                    'end_balance']
                totals_by_column_group[column_group_key]['end_balance_amount'] = partner_values[column_group_key][
                    'end_balance_amount']
                totals_by_column_group[column_group_key]['debit'] += partner_values[column_group_key]['debit']
                totals_by_column_group[column_group_key]['credit'] += partner_values[column_group_key]['credit']
                totals_by_column_group[column_group_key]['balance'] += partner_values[column_group_key]['balance']

            lines.append(self._get_report_line_partners(options, partner, partner_values, level_shift=level_shift))
            # print("TESTLINES", partner, '+', results, '+', partner_values, '+')

        return lines, totals_by_column_group

    def _report_expand_unfoldable_line_partner_ledger_prefix_group(self, line_dict_id, groupby, options, progress,
                                                                   offset, unfold_all_batch_data=None):
        report = self.env['account.report'].browse(options['report_id'])
        matched_prefix = report._get_prefix_groups_matched_prefix_from_line_id(line_dict_id)

        prefix_domain = [('product_id.name', '=ilike', f'{matched_prefix}%')]
        if self._get_no_partner_line_label().upper().startswith(matched_prefix):
            prefix_domain = expression.OR([prefix_domain, [('product_id', '=', None)]])

        expand_options = {
            **options,
            'forced_domain': options.get('forced_domain', []) + prefix_domain
        }
        parent_level = len(matched_prefix) * 2
        partner_lines, dummy = self._build_partner_lines(report, expand_options, level_shift=parent_level)

        for partner_line in partner_lines:
            partner_line['id'] = report._build_subline_id(line_dict_id, partner_line['id'])
            partner_line['parent_id'] = line_dict_id

        lines = report._regroup_lines_by_name_prefix(
            options,
            partner_lines,
            '_report_expand_unfoldable_line_partner_ledger_prefix_group',
            parent_level,
            matched_prefix=matched_prefix,
            parent_line_dict_id=line_dict_id,
        )

        return {
            'lines': lines,
            'offset_increment': len(lines),
            'has_more': False,
        }

    def _caret_options_initializer(self):
        """ Specify caret options for navigating from a report line to the associated journal entry or payment """
        return {
            'stock.move': [{'name': _("View Stock Move"), 'action': 'caret_option_open_record_form'}],
        }

    def _custom_unfold_all_batch_data_generator(self, report, options, lines_to_expand_by_function):
        partner_ids_to_expand = []

        # Regular case
        for line_dict in lines_to_expand_by_function.get('_report_expand_unfoldable_line_partner_ledger', []):
            markup, model, model_id = self.env['account.report']._parse_line_id(line_dict['id'])[-1]
            if model == 'product.product':
                partner_ids_to_expand.append(model_id)
            elif markup == 'no_partner':
                partner_ids_to_expand.append(None)

        # In case prefix groups are used
        no_partner_line_label = self._get_no_partner_line_label().upper()
        partner_prefix_domains = []
        for line_dict in lines_to_expand_by_function.get('_report_expand_unfoldable_line_partner_ledger_prefix_group',
                                                         []):
            prefix = report._get_prefix_groups_matched_prefix_from_line_id(line_dict['id'])
            partner_prefix_domains.append([('name', 'ilike', f'{prefix}%')])

            # amls without partners are regrouped "Unknown Partner", which is also used to create prefix groups
            if no_partner_line_label.startswith(prefix):
                partner_ids_to_expand.append(None)

        if partner_prefix_domains:
            partner_ids_to_expand += self.env['product.product'].search(expression.OR(partner_prefix_domains)).ids

        return {
            'initial_balances': self._get_initial_balance_values(partner_ids_to_expand,
                                                                 options) if partner_ids_to_expand else {},
            'aml_values': self._get_aml_values(options, partner_ids_to_expand) if partner_ids_to_expand else {},
        }

    def action_open_partner(self, options, params):
        dummy, record_id = self.env['account.report']._get_model_info_from_id(params['id'])

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': record_id,
            'views': [[False, 'form']],
            'view_mode': 'form',
            'target': 'current',
        }

    def _query_partners(self, options):
        def assign_sum(row):
            fields_to_assign = ['balance', 'debit', 'credit']
            # if any(not company_currency.is_zero(row[field]) for field in fields_to_assign):
            fields_to_assign = ['open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance',
                                'end_balance_amount', 'balance', 'debit',
                                'main_uom_qty',
                                'credit', 'unit_cost']
            groupby_partners.setdefault(row['groupby'], defaultdict(lambda: defaultdict(float)))
            for field in fields_to_assign:
                if field not in ['open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance',
                                 'end_balance_amount', 'unit_cost']:
                    groupby_partners[row['groupby']][row['column_group_key']][field] += row[field]
                else:
                    groupby_partners[row['groupby']][row['column_group_key']][field] = row[field]

        company_currency = self.env.company.currency_id

        
        query, params = self._get_query_sums(options)
        # print("TESTQUERY", query, '+', params)

        groupby_partners = {}
        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            # print("TESTRES", res)
            product_id = res['groupby']
            move_date = f"{options['date']['date_from']}"
            end_date = f"{options['date']['date_to']} 23:59:59"
            

        totals = {}
        for total_field in ['open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance',
                            'end_balance_amount', 'debit', 'credit', 'balance',
                            'main_uom_qty', 'unit_cost']:
            totals[total_field] = {col_group_key: 0 for col_group_key in options['column_groups']}
            # print("TESTRESssssss1", total_field)
        for row in self._cr.dictfetchall():
            # print("TESTRESssssss2", row)
            totals['main_uom_qty'][row['column_group_key']] += row['main_uom_qty']
            totals['unit_cost'][row['column_group_key']] = row['unit_cost']
            totals['open_balance'][row['column_group_key']] = row['open_balance']
            totals['open_balance_amount'][row['column_group_key']] = row['open_balance_amount']
            totals['stock_in'][row['column_group_key']] = row['stock_in']
            totals['stock_out'][row['column_group_key']] = row['stock_out']
            totals['end_balance'][row['column_group_key']] = row['end_balance']
            totals['end_balance_amount'][row['column_group_key']] = row['end_balance_amount']
            totals['debit'][row['column_group_key']] += row['debit']
            totals['credit'][row['column_group_key']] += row['credit']
            totals['balance'][row['column_group_key']] += row['balance']

            if row['groupby'] not in groupby_partners:
                continue

            assign_sum(row)

        if groupby_partners:
            # Note a search is done instead of a browse to preserve the table ordering.
            partners = self.env['product.product'].with_context(active_test=False).search(
                [('id', 'in', list(groupby_partners.keys()))])
        else:
            partners = []

        # Add 'Partner Unknown' if needed
        if None in groupby_partners.keys():
            partners = [p for p in partners] + [None]
        # print("TESTPARTNER", partners)
        return [(partner, groupby_partners[partner.id if partner else None]) for partner in partners]

    def calculate_opening_stock_sql(self, type, options, product_id, start_date, end_date, opening_stock):
        params = ''
        if type == 'open_balance':
            params += f"""AND sm.effective_done < '{start_date}' """
        else:
            params += f"""AND sm.effective_done >= '{start_date}' AND sm.effective_done <= '{end_date}' """

        if opening_stock is None:
            opening_stock = 0
        out_qty_params = []
        in_qty_params = []
        warehouse_list = options.get('warehouse_ids', [])
        warehouse = False
        all_wh = self.env['stock.warehouse'].search(
            [('active', '=', True), ('lot_stock_id.usage', '=', 'internal')])
        if len(warehouse_list) == 1:
            warehouse = warehouse_list[0]
            params += f"AND (sl.warehouse_id = {warehouse} OR sld.warehouse_id = {warehouse})"
            in_qty_params = f"(sld.warehouse_id = {warehouse})"
            out_qty_params = f"(sl.warehouse_id = {warehouse})"
        elif len(warehouse_list) > 1:
            warehouses = tuple(set(warehouse_list))
            params += f"AND (sl.warehouse_id IN {warehouses} OR sld.warehouse_id IN {warehouses})"
            in_qty_params = f"(sld.warehouse_id IN {warehouses})"
            out_qty_params = f"(sl.warehouse_id IN {warehouses})"
        else:
            params += " "
            in_qty_params = f"(sld.warehouse_id IN {tuple(all_wh.ids)})"
            out_qty_params = f"(sl.warehouse_id IN {tuple(all_wh.ids)})"

        operation_type_list = [record['id'] for record in options.get('operation_type', []) if record['selected']]
        if len(operation_type_list) == 1:
            params += f"AND sm.type_of_operation = '{operation_type_list[0]}'"
        elif len(operation_type_list) > 1:
            operation_type = tuple(set(operation_type_list))
            params += f"AND sm.type_of_operation IN {operation_type}"
        else:
            params += " "

        query = f"""
            WITH stock_data AS (
                SELECT
                    sm.product_id,
                    sm.location_id,
                    sm.location_dest_id,
                    sm.product_uom_qty,
                    CASE
                        WHEN {out_qty_params} THEN sm.product_uom_qty
                        ELSE 0
                    END AS out_qty,
                    CASE
                        WHEN {in_qty_params} THEN sm.product_uom_qty
                        ELSE 0
                    END AS in_qty
                FROM
                    stock_move sm
                    LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
                    LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
                WHERE
                    sm.product_id = {product_id}
                    AND sm.state = 'done'
                    {params}
            )
            SELECT
                SUM(in_qty) AS total_in_qty,
                SUM(out_qty) AS total_out_qty,
                ROUND(({opening_stock} + SUM(in_qty)) - SUM(out_qty), 2) AS opening_stock
            FROM
                stock_data;
            """
        if type == 'open_balance':
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchone()
            return result, result['opening_stock'] if result else opening_stock
        else:
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchone()
            return result, result['opening_stock'] if result else opening_stock

    def _get_query_sums(self, options):
        params = []
        queries = []
        report = self.env.ref('stock_movement_report.stock_mv_report')
        column_groups = report._split_options_per_column_group(options)
        date_from = f"{options['date']['date_from']} 00:00:00"
        date_to = f"{options['date']['date_to']} 23:59:59"
        date_range = (options['date']['date_from'], date_to)

        # Helper function to format lists into SQL conditions
        def format_condition(field, values):
            if type(field) is list:
                if len(values) == 1:
                    column_conditions = [f"{col} = {values[0]}" for col in field]
                    final_condition = f" AND ({' OR '.join(column_conditions)})"
                    return final_condition
                elif values:
                    column_conditions = [f"{col} IN {tuple(values)}" for col in field]
                    final_condition = f" AND ({' OR '.join(column_conditions)})"
                    return final_condition
                return ""
            else:
                if len(values) == 1:
                    return f" AND {field} = {values[0]} "
                elif values:
                    return f" AND {field} IN {tuple(values)} "
                return ""

        # params.append(column_group_key)
        warehouse_list = options.get('warehouse_ids', [])
        from_location_list = options.get('from_location_ids', [])
        to_location_list = options.get('to_location_ids', [])
        selected_op = [record['id'] for record in options.get('operation_type', []) if record['selected']]
        operation_type_list = [f"'{selected_op[0]}'"] if len(selected_op) == 1 else selected_op if len(
            selected_op) > 1 else " "
        # print("TESTQOPTYPE", operation_type_list, '+', len(operation_type_list))

        # Build the account query based on available filters
        account_query = ""
        # ['sm.warehouse_id', 'sl.warehouse_id', 'sld.warehouse_id'] Remove sm.warehouse_id
        account_query += format_condition(['sl.warehouse_id', 'sld.warehouse_id'],
                                          warehouse_list)
        account_query += format_condition('sm.location_id', from_location_list)
        account_query += format_condition('sm.location_dest_id', to_location_list)
        account_query += format_condition('sm.type_of_operation', operation_type_list)

        paramss = ''
        open_paramss = f"""stock_data.sm_date < '{date_from}' """
        end_paramss = f"""sd.sm_date BETWEEN '{date_from}' AND '{date_to}' """

        opening_stock = 0
        out_qty_params = []
        in_qty_params = []
        # warehouse_list = options.get('warehouse_ids', [])
        warehouse = False
        all_wh = self.env['stock.warehouse'].search(
            [('active', '=', True), ('lot_stock_id.usage', '=', 'internal')])
        if len(warehouse_list) == 1:
            warehouse = warehouse_list[0]
            paramss += f" AND (sl.warehouse_id = {warehouse} OR sld.warehouse_id = {warehouse})"
            in_qty_params = f"(sld.warehouse_id = {warehouse})"
            out_qty_params = f"(sl.warehouse_id = {warehouse})"
        elif len(warehouse_list) > 1:
            warehouses = tuple(set(warehouse_list))
            paramss += f" AND (sl.warehouse_id IN {warehouses} OR sld.warehouse_id IN {warehouses})"
            in_qty_params = f"(sld.warehouse_id IN {warehouses})"
            out_qty_params = f"(sl.warehouse_id IN {warehouses})"
        else:
            paramss += ""
            in_qty_params = f"(sld.warehouse_id IN {tuple(all_wh.ids)})"
            out_qty_params = f"(sl.warehouse_id IN {tuple(all_wh.ids)})"

        if len(operation_type_list) == 1:
            paramss += f" AND sm.type_of_operation = {operation_type_list[0]}"
        elif len(operation_type_list) > 1:
            operation_type = tuple(operation_type_list)
            # print("operation_type", operation_type, '+', len(operation_type))
            paramss += f" AND sm.type_of_operation IN {operation_type}"
        else:
            paramss += " "

        # Generate queries for each column group
        for column_group_key, column_group_options in column_groups.items():
            # tables, where_clause, where_params = report._query_get(column_group_options, 'normal')
            # params.extend([column_group_key, column_group_key])
            params += [column_group_key,
                       date_from,
                       date_to,
                       column_group_key,
                       date_from,
                       date_to,
                       ]

            query_template = """
            WITH stock_data AS (
                SELECT
                    sm.product_id AS sda_product_id,
                    sm.location_id,
                    sm.location_dest_id,
                    sm.product_uom_qty,
                    sm.effective_done AS sm_date,
                    CASE
                        WHEN {out_qty_params} THEN sm.product_uom_qty
                        ELSE 0
                    END AS out_qty,
                    CASE
                        WHEN {in_qty_params} THEN sm.product_uom_qty
                        ELSE 0
                    END AS in_qty
                FROM
                    stock_move AS sm
                    LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
                    LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
                WHERE
                    sm.state = 'done'
                    {paramss}
                    ),
            opening_stock_with AS (
            SELECT
                sda_product_id AS ops_product_id,
                SUM(in_qty) AS total_in_qty,
                SUM(out_qty) AS total_out_qty,
                ROUND(({opening_stock} + SUM(in_qty)) - SUM(out_qty), 2) AS opening_stock
            FROM
                stock_data
                WHERE 
                {open_paramss}
                 Group By ops_product_id),
                 
            closing_stock_with AS (
            SELECT
                ops.ops_product_id AS ops_product_id,
				sd.sda_product_id AS sda_product_id,
                SUM(sd.in_qty) AS total_in_qty,
                SUM(sd.out_qty) AS total_out_qty,
                ROUND((ops.opening_stock + SUM(sd.in_qty)) - SUM(sd.out_qty), 2) AS end_stock
            FROM
                stock_data AS sd
                LEFT JOIN opening_stock_with AS ops ON ops.ops_product_id = sd.sda_product_id
                WHERE {end_paramss}
                 Group By ops_product_id,sda_product_id,ops.opening_stock)
                
                SELECT * FROM (
                    SELECT
                        sm.product_id AS groupby,
                        %s AS column_group_key,
                        sm.effective_done AS move_date,
                        CASE
                            WHEN sm.product_uom_qty != 0 AND aml.account_id = p.property_stock_valuation_account_id THEN am.main_qty_main_uom
                            ELSE 0
                        END AS main_uom_qty,
                        CASE
                            WHEN aml.balance != 0.00 AND sm.product_uom_qty != 0.00 THEN (ABS(aml.balance) / sm.product_uom_qty)
                            ELSE 0
                        END AS unit_cost,
                        CASE
                            WHEN aml.account_id IN (p.property_stock_valuation_account_id, p.property_account_expense_categ_id) THEN aml.debit
                            ELSE 0
                        END AS debit,
                        CASE
                            WHEN aml.account_id IN (p.property_stock_valuation_account_id, p.property_account_expense_categ_id) THEN aml.credit
                            ELSE 0
                        END AS credit,
                        CASE
                            WHEN aml.balance != 0 THEN aml.balance
                            ELSE 0
                        END AS balance,
                        (SELECT
                opening_stock
            FROM
                opening_stock_with WHERE ops_product_id = sm.product_id) AS open_balance,
                SUM(((SELECT
                opening_stock
            FROM
                opening_stock_with WHERE ops_product_id = sm.product_id)) * unit_cost) AS open_balance_amount,
                (SELECT
                total_in_qty
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id) AS stock_in,
                (SELECT
                total_out_qty
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id) AS stock_out,
                (SELECT
                end_stock
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id) AS end_balance,
                SUM(((SELECT
                end_stock
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id)) * unit_cost) AS end_balance_amount
                
                    FROM stock_move AS sm
                    JOIN account_move AS am ON am.stock_move_id = sm.id
                    LEFT JOIN product_product p ON sm.product_id = p.id
                    LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
                    LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
                    LEFT JOIN account_move_line AS aml ON aml.move_id = am.id AND aml.account_id IN (p.property_stock_valuation_account_id, p.property_account_expense_categ_id)
                    WHERE sm.state = 'done'
                        AND sm.effective_done BETWEEN %s AND %s
                        {account_query}
                    GROUP BY sm.product_id, aml.account_id, p.property_stock_valuation_account_id, p.property_account_expense_categ_id, aml.debit, aml.credit, aml.balance, am.main_qty_main_uom,sm.product_uom_qty, move_date
                    UNION ALL
                    SELECT
                        sm.product_id AS groupby,
                        %s AS column_group_key,
                        sm.effective_done AS move_date,
                        sum(sm.product_uom_qty) AS main_uom_qty,
                        sm.unit_cost AS unit_cost,
                        0 AS debit,
                        0 AS credit,
                        0 AS balance,
                        (SELECT
                opening_stock
            FROM
                opening_stock_with WHERE ops_product_id = sm.product_id) AS open_balance,
                SUM(((SELECT
                opening_stock
            FROM
                opening_stock_with WHERE ops_product_id = sm.product_id)) * unit_cost) AS open_balance_amount,
                (SELECT
                total_in_qty
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id) AS stock_in,
                (SELECT
                total_out_qty
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id) AS stock_out,
                (SELECT
                end_stock
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id) AS end_balance,
                SUM(((SELECT
                end_stock
            FROM
                closing_stock_with WHERE sda_product_id = sm.product_id)) * unit_cost) AS end_balance_amount
                    FROM stock_move AS sm
                    LEFT JOIN product_product p ON sm.product_id = p.id
                    LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
                    LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
                    WHERE sm.account_move_exist IS NOT TRUE AND sm.state = 'done' AND sm.effective_done BETWEEN %s AND %s
                        {account_query}
                    GROUP BY sm.product_id, p.property_stock_valuation_account_id, sm.product_uom_qty, sm.unit_cost, move_date
                ) AS combined_results
                ORDER BY move_date ASC
            """
            query = query_template.format(account_query=account_query, out_qty_params=out_qty_params,
                                          in_qty_params=in_qty_params, paramss=paramss, opening_stock=opening_stock,
                                          open_paramss=open_paramss, end_paramss=end_paramss)
            queries.append(query)
            # print("QQ", query, '+', params)

        # return queries, params
        return ' UNION ALL '.join(queries), params

    def _get_initial_balance_values(self, partner_ids, options):
        """
        Construct a query retrieving all the aggregated sums to build the report.
        It includes sums for all partners and sums for the initial balances.

        :param partner_ids: List of partner IDs.
        :param options: The report options.
        :return: (query, params)
        """
        params = []
        queries = []
        report = self.env.ref('stock_movement_report.stock_mv_report')

        # Create the currency table query
        # ct_query = self.env['res.currency']._get_query_currency_table(options)

        column_groups = report._split_options_per_column_group(options)
        date_from = f"{options['date']['date_from']} 00:00:00"
        date_to = f"{options['date']['date_to']} 23:59:59"
        date_range = (options['date']['date_from'], date_to)

        # Helper function to format lists into SQL conditions
        def format_condition(field, values):
            if len(values) == 1:
                return f" AND {field} = {values[0]}"
            elif values:
                return f" AND {field} IN {tuple(values)}"
            return ""

        # Helper function to build account query
        def build_account_query(warehouse_list, from_location_list, to_location_list, operation_type_list):
            account_query = ""
            account_query += format_condition('sm.warehouse_id', warehouse_list)
            account_query += format_condition('sl.warehouse_id', warehouse_list)
            account_query += format_condition('sld.warehouse_id', warehouse_list)
            account_query += format_condition('sm.location_id', from_location_list)
            account_query += format_condition('sm.location_dest_id', to_location_list)
            account_query += format_condition('sm.type_of_operation', operation_type_list)
            return account_query

        # Helper function to generate queries
        def generate_queries(column_group_key, date_from, date_to, warehouse_list, from_location_list,
                             to_location_list, operation_type_list):
            account_query = build_account_query(warehouse_list, from_location_list, to_location_list,
                                                operation_type_list)
            product_condition = format_condition('sm.product_id', partner_ids)
            common_select = f"""
            SELECT * FROM (
                SELECT
                    sm.product_id        ,
                    %s AS column_group_key,
                    sm.effective_done AS move_date,
                    CASE
                        WHEN sm.product_uom_qty != 0 AND aml.account_id = p.property_stock_valuation_account_id THEN am.main_qty_main_uom
                        ELSE 0
                    END AS main_uom_qty,
                    CASE
                        WHEN aml.balance != 0.00 AND sm.product_uom_qty != 0.00 THEN (ABS(aml.balance) / sm.product_uom_qty)
                        ELSE 0
                    END AS unit_cost,
                    CASE
                        WHEN aml.account_id IN (p.property_stock_valuation_account_id, p.property_account_expense_categ_id) THEN aml.debit
                        ELSE 0
                    END AS debit,
                    CASE
                        WHEN aml.account_id IN (p.property_stock_valuation_account_id, p.property_account_expense_categ_id) THEN aml.credit
                        ELSE 0
                    END AS credit,
                    CASE
                        WHEN aml.balance != 0 THEN aml.balance
                        ELSE 0
                    END AS balance
                FROM stock_move AS sm
                JOIN account_move AS am ON am.stock_move_id = sm.id
                LEFT JOIN product_product p ON sm.product_id = p.id
                LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
                LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
                LEFT JOIN account_move_line AS aml ON aml.move_id = am.id AND aml.account_id IN (p.property_stock_valuation_account_id, p.property_account_expense_categ_id)
                WHERE sm.state = 'done'
                    AND sm.effective_done BETWEEN '{date_from}' AND '{date_to}'
                    {account_query}
                    {product_condition}
                GROUP BY sm.product_id, aml.account_id, p.property_stock_valuation_account_id, p.property_account_expense_categ_id, aml.debit, aml.credit, aml.balance, am.main_qty_main_uom,sm.product_uom_qty, move_date
                UNION ALL
                SELECT
                    sm.product_id        ,
                    %s AS column_group_key,
                    sm.effective_done AS move_date,
                    sm.product_uom_qty AS main_uom_qty,
                    sm.unit_cost AS unit_cost,
                    0 AS debit,
                    0 AS credit,
                    0 AS balance
                FROM stock_move AS sm
                LEFT JOIN product_product p ON sm.product_id = p.id
                LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
                LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
                WHERE sm.account_move_exist IS NOT TRUE AND sm.state = 'done' AND sm.effective_done BETWEEN '{date_from}' AND '{date_to}'
                    {account_query}
                    {product_condition}
                GROUP BY sm.product_id, p.property_stock_valuation_account_id, sm.product_uom_qty, sm.unit_cost, move_date)AS combined_results
                ORDER BY move_date ASC
            """
            return common_select

        # Generate queries for each column group
        for column_group_key, column_group_options in column_groups.items():
            new_options = self._get_options_initial_balance(column_group_options)
            # tables, where_clause, where_params = report._query_get(new_options, 'normal',
            #                                                        domain=[('product_id', 'in', partner_ids)])
            # params.extend([column_group_key, column_group_key])
            params += [column_group_key,
                       column_group_key,
                       ]

            warehouse_list = options.get('warehouse_ids', [])
            from_location_list = options.get('from_location_ids', [])
            to_location_list = options.get('to_location_ids', [])
            selected_op = [record['id'] for record in options.get('operation_type', []) if record['selected']]
            operation_type_list = [f"'{selected_op[0]}'"] if len(selected_op) == 1 else selected_op if len(
                selected_op) > 1 else " "

            query = generate_queries(column_group_key, date_from, date_to, warehouse_list,
                                     from_location_list, to_location_list, operation_type_list)
            queries.append(query)

        self._cr.execute(" UNION ALL ".join(queries), params)

        init_balance_by_col_group = {
            product_id: {column_group_key: {} for column_group_key in options['column_groups']}
            for product_id in partner_ids
        }
        for result in self._cr.dictfetchall():
            if result['product_id'] in partner_ids:
                init_balance_by_col_group[result['product_id']][result['column_group_key']] = result

        return init_balance_by_col_group
        # return final_query, params

    def _report_expand_unfoldable_line_partner_ledger(self, line_dict_id, groupby, options, progress, offset,
                                                      unfold_all_batch_data=None):
        def init_load_more_progress(line_dict):
            return {
                column['column_group_key']: line_col.get('no_format', 0)
                for column, line_col in zip(options['columns'], line_dict['columns'])
                if column['expression_label'] == 'balance'
            }

        report = self.env.ref('stock_movement_report.stock_mv_report')
        markup, model, record_id = report._parse_line_id(line_dict_id)[-1]

        if model != 'product.product':
            raise UserError(_("Wrong ID for partner ledger line to expand: %s", line_dict_id))

        prefix_groups_count = 0
        for markup, dummy1, dummy2 in report._parse_line_id(line_dict_id):
            if markup.startswith('groupby_prefix_group:'):
                prefix_groups_count += 1
        level_shift = prefix_groups_count * 2

        lines = []

        # Get initial balance
        if offset == 0:
            if unfold_all_batch_data:
                init_balance_by_col_group = unfold_all_batch_data['initial_balances'][record_id]
            else:
                init_balance_by_col_group = self._get_initial_balance_values([record_id], options)[record_id]
            initial_balance_line = report._get_partner_and_general_ledger_initial_balance_line(options, line_dict_id,
                                                                                               init_balance_by_col_group,
                                                                                               level_shift=level_shift)
            if initial_balance_line:
                lines.append(initial_balance_line)

                # For the first expansion of the line, the initial balance line gives the progress
                progress = init_load_more_progress(initial_balance_line)

        limit_to_load = report.load_more_limit + 1 if report.load_more_limit and not self._context.get(
            'print_mode') else None

        if unfold_all_batch_data:

            aml_results = unfold_all_batch_data['aml_values'][record_id]

        else:

            aml_results = self._get_aml_values(options, [record_id], offset=offset, limit=limit_to_load)[record_id]

        has_more = False
        treated_results_count = 0
        next_progress = progress
        for result in aml_results:
            if not self._context.get(
                    'print_mode') and report.load_more_limit and treated_results_count == report.load_more_limit:
                # We loaded one more than the limit on purpose: this way we know we need a "load more" line
                has_more = True
                break

            new_line = self._get_report_line_move_line(options, result, line_dict_id, next_progress,
                                                       level_shift=level_shift)
            lines.append(new_line)
            next_progress = init_load_more_progress(new_line)
            treated_results_count += 1

        return {
            'lines': lines,
            'offset_increment': treated_results_count,
            'has_more': has_more,
            'progress': json.dumps(next_progress)
        }

    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        def build_account_query(warehouse_list, from_location_list, to_location_list, operation_type_list):
            query_parts = []
            if warehouse_list:
                warehouse_query = build_warehouse_query(warehouse_list)
                query_parts.append(warehouse_query)
            if from_location_list:
                from_location_query = build_location_query('sm.location_id', from_location_list)
                query_parts.append(from_location_query)
            if to_location_list:
                to_location_query = build_location_query('sm.location_dest_id', to_location_list)
                query_parts.append(to_location_query)
            if operation_type_list:
                operation_type_query = build_operation_type_query(operation_type_list)
                query_parts.append(operation_type_query)
            return " ".join(query_parts)

        def build_operation_type_query(operation_type_list):
            if len(operation_type_list) == 1:
                return f"AND sm.type_of_operation = '{operation_type_list[0]}'"
            operation_type = tuple(set(operation_type_list))
            return f"AND sm.type_of_operation IN {tuple(set(operation_type))}"

        def build_warehouse_query(warehouse_list):
            if len(warehouse_list) == 1:
                warehouse = warehouse_list[0]
                # f"AND (sm.warehouse_id = {warehouse} OR sl.warehouse_id = {warehouse} OR sld.warehouse_id = {warehouse})" Remove sm.warehouse_id
                return f"AND (sl.warehouse_id = {warehouse} OR sld.warehouse_id = {warehouse})"
            warehouses = tuple(set(warehouse_list))
            return f"AND (sl.warehouse_id IN {warehouses} OR sld.warehouse_id IN {warehouses})"

        def build_location_query(column, location_list):
            if len(location_list) == 1:
                location = location_list[0]
                return f"AND {column} = {location}"
            locations = tuple(set(location_list))
            return f"AND {column} IN {locations}"

        rslt = {product_id: [] for product_id in partner_ids}
        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        directly_linked_aml_partner_params = []

        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append('sm.product_id IN %s')
            directly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))

        directly_linked_aml_partner_clause = '(' + ' OR '.join(directly_linked_aml_partner_clauses) + ')'
        # ct_query = self.env['res.currency']._get_query_currency_table(options)
        queries = []
        all_params = []

        lang = self.env.lang or get_lang(self.env).code
        journal_name = f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')" if self.pool[
            'account.journal'].name.translate else 'journal.name'
        account_name = f"COALESCE(account.name->>'{lang}', account.name->>'en_US')" if self.pool[
            'account.account'].name.translate else 'account.name'
        report = self.env.ref('stock_movement_report.stock_mv_report')
        uom_name = f"COALESCE(uom.name->>'{lang}', uom.name->>'en_US')"
        date_from = options['date']['date_from'] + ' 00:00:00'
        date_to = options['date']['date_to'] + ' 23:59:59'

        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            # tables, where_clause, where_params = report._query_get(group_options, 'strict_range')
            all_params += [column_group_key, *directly_linked_aml_partner_params, column_group_key,
                           *directly_linked_aml_partner_params]

            warehouse_list = options.get('warehouse_ids', [])
            from_location_list = options.get('from_location_ids', [])
            to_location_list = options.get('to_location_ids', [])
            operation_type_list = [record['id'] for record in options.get('operation_type', []) if record['selected']]

            account_query = build_account_query(warehouse_list, from_location_list, to_location_list,
                                                operation_type_list)
            
            query = f'''
            SELECT * FROM (
            SELECT
                sm.id, sm.product_id, sm.reference AS move_name, sm.picking_contact_name AS picking_contact_name,
                sl.complete_name AS from_date, sld.complete_name AS to_date, sm.effective_done AS move_date,
                {uom_name} AS uom, am.main_qty_main_uom AS main_uom_qty,
                CASE WHEN aml.balance != 0.00 AND sm.product_uom_qty != 0.00 THEN (abs(aml.balance) / sm.product_uom_qty) ELSE 0 END AS unit_cost,
                CASE WHEN aml.account_id = p.property_stock_valuation_account_id AND aml.debit != 0 THEN aml.debit ELSE 0 END AS debit,
                CASE WHEN aml.account_id = p.property_stock_valuation_account_id AND aml.credit != 0 THEN aml.credit ELSE 0 END AS credit,
                aml.balance AS balance, %s AS column_group_key, 'directly_linked_aml' AS key
            FROM stock_move AS sm
            LEFT JOIN product_product p ON sm.product_id = p.id
            JOIN account_move AS am ON am.stock_move_id = sm.id
            LEFT JOIN account_move_line AS aml ON aml.move_id = am.id AND aml.account_id = p.property_stock_valuation_account_id
            LEFT JOIN res_company AS res_comp ON res_comp.id = sm.company_id
            LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
            LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
            LEFT JOIN product_template tmpl ON p.product_tmpl_id = tmpl.id
            LEFT JOIN product_category cat on cat.id = tmpl.categ_id
            LEFT JOIN uom_uom uom on uom.id = tmpl.uom_id
            WHERE sm.state = 'done' {account_query}
             AND aml.balance IS NOT NULL
             AND {directly_linked_aml_partner_clause}
            UNION ALL
            SELECT
                sm.id, sm.product_id, sm.reference AS move_name, sm.picking_contact_name AS picking_contact_name,
                sl.complete_name AS from_date, sld.complete_name AS to_date, sm.effective_done AS move_date,
                {uom_name} AS uom, sm.product_uom_qty AS main_uom_qty, sm.unit_cost AS unit_cost,
                0 AS debit, 0 AS credit, 0 AS balance, %s AS column_group_key, 'directly_linked_aml' AS key
            FROM stock_move AS sm
            LEFT JOIN product_product p ON sm.product_id = p.id
            LEFT JOIN stock_location AS sl ON sl.id = sm.location_id
            LEFT JOIN stock_location AS sld ON sld.id = sm.location_dest_id
            LEFT JOIN product_template tmpl ON p.product_tmpl_id = tmpl.id
            LEFT JOIN uom_uom uom on uom.id = tmpl.uom_id
            WHERE sm.account_move_exist IS NOT TRUE AND sm.state = 'done' 
            AND sm.product_uom_qty > 0
            {account_query} AND {directly_linked_aml_partner_clause}
            )AS combined_results
            WHERE move_date >= '{date_from}' AND move_date <= '{date_to}'
                ORDER BY move_date ASC 
            '''
            queries.append(query)
        query = '(' + ') UNION ALL ('.join(queries) + ')'
        if offset:
            query += ' OFFSET %s '
            all_params.append(offset)

        if limit:
            query += ' LIMIT %s '
            all_params.append(limit)
        # Execute queries and process results
        # for query1 in query:
        # print("TESTQWE", query, '+', all_params)
        self.env.cr.execute(query, all_params)
        for row in self.env.cr.dictfetchall():
            product_id = row['product_id']
            move_date = row['move_date']
            unit_cost = row['unit_cost']
            end_date = date_to
            # from_location_id = row['from_location_id']
            # to_location_id = row['to_location_id']

            # Calculate opening stock for the from location
            open_res, open_balance = self.calculate_opening_stock_sql('open_balance', options, product_id, move_date,
                                                                      0, 0)
            result, end_balance = self.calculate_opening_stock_sql('end_balance', options, product_id, move_date,
                                                                   move_date,
                                                                   open_balance if open_balance else 0)

            # Include opening_stock in the result
            row['open_balance'] = open_balance
            row['open_balance_amount'] = (open_balance if open_balance else 0) * (unit_cost if unit_cost else 0)
            row['stock_in'] = result['total_in_qty']
            row['stock_out'] = result['total_out_qty']
            row['end_balance'] = end_balance
            row['end_balance_amount'] = (end_balance * unit_cost) if end_balance and unit_cost else 0
            rslt[product_id].append(row)
            # rslt[row['product_id']].append(row)
        # print("TESTRSLT",rslt)
        return rslt

    def _get_report_line_partners(self, options, partner, partner_values, level_shift=0):
        company_currency = self.env.company.currency_id
        unfold_all = (self._context.get('print_mode') and not options.get('unfolded_lines')) or options.get(
            'unfold_all')

        unfoldable = False
        column_values = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_expr_label = column['expression_label']
            value = partner_values[column['column_group_key']].get(col_expr_label)

            if col_expr_label in {'open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance',
                                  'end_balance_amount', 'main_uom_qty', 'unit_cost',
                                  'debit', 'credit', 'balance'}:
                formatted_value = report.format_value(options,value, figure_type=column['figure_type'],
                                                      blank_if_zero=column['blank_if_zero'])
            else:
                formatted_value = report.format_value(options,value,
                                                      figure_type=column['figure_type']) if value is not None else value

            unfoldable = unfoldable or (col_expr_label in (
                'open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance', 'end_balance_amount',
                'main_uom_qty', 'unit_cost', 'debit',
                'credit'))

            if col_expr_label == 'debit':
                col_class = 'number color-green'
            elif col_expr_label == 'credit':
                col_class = 'number color-red'
            else:
                col_class = 'number'

            column_values.append({
                'name': formatted_value,
                'no_format': value,
                'class': col_class
            })

        line_id = report._get_generic_line_id('product.product',
                                              partner.id) if partner else report._get_generic_line_id(
            'product.product', None, markup='no_partner')
        return {
            'id': line_id,
            'name': partner.with_context(lang=self.env.user.lang) is not None and (partner.with_context(
                lang=self.env.user.lang).display_name or '')[:128] or self._get_no_partner_line_label(),
            'columns': column_values,
            'level': 1 + level_shift,
            'unfoldable': unfoldable,
            'unfolded': line_id in options['unfolded_lines'] or unfold_all,
            'expand_function': '_report_expand_unfoldable_line_partner_ledger',
        }

    def _get_no_partner_line_label(self):
        return _('Unknown Product')

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group,
                                   level_shift=0):
        caret_type = 'stock.move'

        columns = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_expr_label = column['expression_label']
            # if col_expr_label == 'move_name':
            #     col_value = report._format_aml_name(aml_query_result['move_name'])
            # else:
            col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result[
                'column_group_key'] else None

            if col_value is None:
                columns.append({})
            else:
                col_class = 'number'

                if col_expr_label == 'move_date':
                    formatted_value = format_date(self.env, fields.Date.from_string(col_value))
                    col_class = 'date'
                elif col_expr_label == 'amount_currency':
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    formatted_value = report.format_value(options,col_value, currency=currency,
                                                          figure_type=column['figure_type'])
                elif col_expr_label == 'balance':
                    col_value += init_bal_by_col_group[column['column_group_key']]
                    formatted_value = report.format_value(options,col_value, figure_type=column['figure_type'],
                                                          blank_if_zero=column['blank_if_zero'])
                else:
                    if col_expr_label == 'debit':
                        col_class = 'color-green'
                    elif col_expr_label == 'credit':
                        col_class = 'color-red'
                    elif col_expr_label == 'ref':
                        col_class = 'o_account_report_line_ellipsis'
                    elif col_expr_label not in (
                            'open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance',
                            'end_balance_amount', 'main_uom_qty', 'unit_cost',
                            'debit',
                            'credit'):
                        col_class = ''
                    formatted_value = report.format_value(options,col_value, figure_type=column['figure_type'])
                if aml_query_result['debit'] > 0:
                    columns.append({
                        'name': formatted_value,
                        'no_format': col_value,
                        'class': 'color-green',
                    })
                elif aml_query_result['credit'] > 0:
                    columns.append({
                        'name': formatted_value,
                        'no_format': col_value,
                        'class': 'color-red',
                    })
                else:
                    columns.append({
                        'name': formatted_value,
                        'no_format': col_value,
                        'class': '',
                    })

        return {
            'id': report._get_generic_line_id('stock.move', aml_query_result['id'],
                                              parent_line_id=partner_line_id),
            'parent_id': partner_line_id,
            'name': format_date(self.env, aml_query_result['move_date']),
            'class': 'text-muted' if aml_query_result['key'] == 'indirectly_linked_aml' else 'text',
            # do not format as date to prevent text centering
            'columns': columns,
            'caret_options': caret_type,
            'level': 3 + level_shift,
        }

    def _get_report_line_total(self, options, totals_by_column_group):
        column_values = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_expr_label = column['expression_label']
            value = totals_by_column_group[column['column_group_key']].get(column['expression_label'])

            if col_expr_label in {'open_balance', 'open_balance_amount', 'stock_in', 'stock_out', 'end_balance',
                                  'end_balance_amount', 'main_uom_qty', 'unit_cost',
                                  'debit', 'credit', 'balance'}:
                formatted_value = report.format_value(options,value, figure_type=column['figure_type'], blank_if_zero=False)
            else:
                formatted_value = report.format_value(options,value, figure_type=column['figure_type']) if value else None

            if col_expr_label == 'debit':
                col_class = 'number color-green'
            elif col_expr_label == 'credit':
                col_class = 'number color-red'
            else:
                col_class = 'number'

            column_values.append({
                'name': formatted_value,
                'no_format': value,
                'class': col_class
            })

        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': column_values,
        }
