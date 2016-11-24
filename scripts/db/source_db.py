import abc


class BaseDB(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_in_both(self, day_date):
        """Do something"""

    @abc.abstractmethod
    def get_elsewhere_only(self, day_date):
        """Do something"""

    @abc.abstractmethod
    def get_uom_only(self, day_date):
        """Do something"""

    @abc.abstractmethod
    def get_count_of_others_at_uom(self, day_date):
        """Do something"""

    @abc.abstractmethod
    def get_allocated_totals(self, day_date):
        """Do something"""

    @abc.abstractmethod
    def get_used_data(self, day_date):
        """Do something"""

    @abc.abstractmethod
    def get_top_twenty_projects(self, day_date):
        """"""

    @abc.abstractmethod
    def get_uom_project_contact_email(self):
        """
        :return:
            A list giving the email address of the project contact
            in the allocation database for all projects that are deemed to
            belong to UoM
        """

    @abc.abstractmethod
    def count_instances_since(self, start_day):
        """
        :return:
            The number of instances launched since start day date.
        """

    @abc.abstractmethod
    def get_cell_names(self):
        """
        :return:
            The set of the cell names in the reporting database
        """