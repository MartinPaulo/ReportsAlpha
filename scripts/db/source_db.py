"""
An abstract class to allow us to switch between the reporting db and the
production db's
"""
from abc import ABCMeta
from abc import abstractmethod


class BaseDB(metaclass=ABCMeta):
    @abstractmethod
    def get_allocated_totals(self, day_date):
        """Do something"""

    @abstractmethod
    def get_used_data(self, day_date):
        """Do something"""

    @abstractmethod
    def get_top_twenty_projects(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The top twenty UoM projects by vcpu count on day_date.
        """

    @abstractmethod
    def get_uom_project_contact_email(self):
        """
        :return:
            A list giving the email address of the project contact
            in the allocation database for all projects that are deemed to
            belong to UoM
        """

    @abstractmethod
    def count_instances_since(self, start_day):
        """
        :return:
            The number of instances launched since start day date.
        """

    @abstractmethod
    def get_cell_names(self):
        """
        :return:
            The set of the cell names in the reporting database
        """

    @abstractmethod
    def get_all_outside(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The number of users in UoM projects who are running instances
        outside of UoM data centers on day_date.
        """

    @abstractmethod
    def get_elsewhere_only(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The number of users in UoM projects who are running instances
            only in data centers that do not belong to UoM on day_date.
        """

    @abstractmethod
    def get_in_both(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The count of users in UoM projects running instances in
        both UoM and non UoM data centers on day_date.

        Notes:
            Instances started and stopped on the day are *included*.
            Trial Projects are included.
            This method is *slow*!
        """

    @abstractmethod
    def get_uom_only(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The number of users in UoM projects who have run instances
        only in the  UoM data centers on day_date.
        """

    @abstractmethod
    def get_count_of_others_at_uom(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The count of users who belong to non-UoM projects running
        instances in UoM data centers on day_date
        """

    @abstractmethod
    def get_private_cell_data(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The projects using Melbourne's private cell on the given
        day
        """