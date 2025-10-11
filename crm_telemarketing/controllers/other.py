@http.route('/telemarketing_dashboard/charts_data', type='json', auth='user')
def get_charts_data(self, **kw):
    """ Get charts data for the telemarketor_dashboard dashboard. """
    TelemarketingReport = request.env['report.telemarketor_dashboard']

    # Query to get calls by user and their count
    calls_by_user = TelemarketingReport.read_group(
        domain=[],
        fields=['user_id', 'total_calls'],
        groupby=['user_id'],
        orderby='user_id',
    )

    # Query to get calls by status
    calls_by_status = TelemarketingReport.read_group(
        domain=[],
        fields=['status_id', 'total_calls'],
        groupby=['status_id'],
    )

    # Process data for calls by user
    calls_by_user_data = {
        rec['user_id'][1]: rec['total_calls'] for rec in calls_by_user
    }

    # Process data for calls by status
    calls_by_status_data = {
        rec['status_id'][1]: rec['total_calls'] for rec in calls_by_status
    }

    return {
        'calls_by_user': calls_by_user_data,
        'calls_by_status': calls_by_status_data
    }