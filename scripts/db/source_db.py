"""
An abstract class to allow us to switch between the reporting db and the
production db's
"""
from abc import ABCMeta
from abc import abstractmethod


class BaseDB(metaclass=ABCMeta):
    @abstractmethod
    def get_allocated_totals(self, day_date):
        """
        :param day_date: The day up till which data is to be returned.
        :return: The amount allocated in keystone for those projects whose
        last modified date is less than or equal to the day_date.

        Notes:
            Because these are allocations, personal projects are automatically
            excluded (they don't go through the allocation process)
        """

    @abstractmethod
    def get_used_data(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The sum of the the vcpu's being used by UoM projects
        on the given day.

        Notes:
            Personal projects are excluded.
            Instances started and stopped on the day are also excluded.
        """

    @abstractmethod
    def get_top_twenty_projects(self, day_date):
        """
        :param day_date: The day for which the query is to be run
        :return: The top twenty UoM projects by vcpu count on day_date.
        """

    @abstractmethod
    def get_uom_project_contact_details(self):
        """
        :return:
            A list giving the details of the project contact
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

    @abstractmethod
    def get_projects_active(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            int: The count of projects active between the start and end dates
        """

    @abstractmethod
    def get_uom_projects_active(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            int: The count of UoM owned approved projects active between the
            start and end dates
        """

    @abstractmethod
    def get_all_uom_projects_active(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            int: The count of all UoM owned projects (includes personal ones)
            active between the start and end dates
        """

    @abstractmethod
    def get_projects_active_with_uom_participation(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            int: The count of projects active between the start and
            end dates that have UoM participants
        """

    @abstractmethod
    def get_admins_active(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            int: The count of all users active between the start and
            end dates
        """

    @abstractmethod
    def get_uom_users_active(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            int: The count of UoM user active between the start and
            end dates
        """

    @abstractmethod
    def get_email_of_active_uom_users(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            DictCursor: A list of the email addresses of UoM users who were
            active between the start and end dates
        """

    @abstractmethod
    def get_core_hours(self, from_date, to_date):
        """
        Args:
            from_date (date): The start date
            to_date (date): The end date

        Returns:
            DictCursor: A list containing each projects core hours usage
            between the start date and the end date
        """
