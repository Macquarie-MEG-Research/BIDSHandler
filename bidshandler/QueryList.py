class QueryList(list):
    """
    List wrapper class to allow the list of return objects from a query to
    itself be queried.

    """
    def __init__(self, *iterable):
        super(QueryList, self).__init__(*iterable)

#region public methods

    def query(self, obj, token, condition, value):
        """
        Query the BIDS object and return the appropriate data.

        Parameters
        ----------
        obj : str
            The object type that should be returned.
            This can be one of ('project', 'subject', 'session', 'scan')
        token : str
            The key to query for. This can be a value from the following list:

            - **task**: Corresponds to the `task` key in the BIDS filename.
            - **acquisition** or **acq**: Corresponds to the `acq` key in the
              BIDS filename.
            - **run**: Corresponds to the `run` key in the BIDS filename.
            - **proc**: Corresponds to the `proc` key in the BIDS filename.
            - **age**: Corresponds to the age of the participant.
              [Only available for `obj='subject'`]
            - **sex**: Corresponds to the gender of the participant.
              [Only available for `obj='subject'`]
            - **group**: Corresponds to the group of the participant.
              [Only available for `obj='subject'`]
            - **rec_date**: Corresponds to the time and date of the recording.
              The value can either be formatted like "%Y-%m-%d"
              (ie. YYYY-MM-DD) to specify a single day, or it can be
              specified to the second by formatting it using the format
              string "%Y-%m-%dT%H:%M:%S" (ie. YYYY-MM-DDTHH:mm:ss).
            - **subjects**: Corresponds to the number of subjects contained.
              [Only available for `obj='project'`]
            - **sessions**: Corresponds to the number of sessions contained.
              [Only available for `obj='project'` or `'subject'`]
            - **scans**: Corresponds to the number of scans contained.
              [Only available for `obj='project'`, `'subject'` or
              `'session'`]
            - Any other token will be considered to be a key in the
              sidecar.json file.
        condition : str
            One of ('<', '<=', '=', '!=', '!!=' (none equal), '=>', '>').
            Used to perform comaprisons between the value provided and the
            values the data have.
            The '!!=' operator here is used to distinguish between the case of
            when you want to determine if something contains something that
            isn't the value you specify, and whether something doesn't contain
            the value specified.
            This operator is currently only supported for the tokens `'task'`,
            `'acquisition'`/`'acq', `'run'` and `'proc'`.
        value : str | int | float
            The value the token has (or the value to compare using the
            `condition` argument)
            The value provided must match exactly if the equality operator is
            used, and must have a type appropriate for comparison if an
            inequality operator is used.
            Currently regex is not supported, but this may come in the future.

        Returns
        -------
        return_data : :py:class:`bidshandler.QueryList`
            List of objects that satisfy the provided query conditions.
        """

        return_data = QueryList()
        for BIDSobj in self:
            return_data.extend(BIDSobj.query(obj, token, condition, value))
        return return_data
