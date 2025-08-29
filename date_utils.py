#!/usr/bin/env python3
"""
Date utilities module for CRM Legal
Handles date formatting and conversion between Argentine format (DD-MM-YYYY) and ISO format (YYYY-MM-DD)
"""

import datetime
from typing import Union, Optional


class DateFormatter:
    """Utility class for date formatting and conversion"""
    
    # Date format constants
    ARGENTINE_FORMAT = "%d-%m-%Y"  # DD-MM-YYYY
    ISO_FORMAT = "%Y-%m-%d"        # YYYY-MM-DD
    DISPLAY_FORMAT = "%d/%m/%Y"    # DD/MM/YYYY for display
    
    @staticmethod
    def to_display_format(date_value: Union[str, datetime.date, datetime.datetime, None]) -> str:
        """
        Converts any date format to DD/MM/YYYY for display in Argentine format
        
        Args:
            date_value: Date in various formats (string, date object, datetime object, or None)
            
        Returns:
            str: Date in DD/MM/YYYY format, or empty string if invalid
        """
        if date_value is None:
            return ""
            
        try:
            # If it's already a date or datetime object
            if isinstance(date_value, (datetime.date, datetime.datetime)):
                return date_value.strftime(DateFormatter.DISPLAY_FORMAT)
            
            # If it's a string, try to parse it
            if isinstance(date_value, str):
                date_value = date_value.strip()
                if not date_value:
                    return ""
                
                # Try ISO format first (YYYY-MM-DD)
                try:
                    parsed_date = datetime.datetime.strptime(date_value, DateFormatter.ISO_FORMAT).date()
                    return parsed_date.strftime(DateFormatter.DISPLAY_FORMAT)
                except ValueError:
                    pass
                
                # Try Argentine format (DD-MM-YYYY)
                try:
                    parsed_date = datetime.datetime.strptime(date_value, DateFormatter.ARGENTINE_FORMAT).date()
                    return parsed_date.strftime(DateFormatter.DISPLAY_FORMAT)
                except ValueError:
                    pass
                
                # Try display format (DD/MM/YYYY)
                try:
                    parsed_date = datetime.datetime.strptime(date_value, DateFormatter.DISPLAY_FORMAT).date()
                    return parsed_date.strftime(DateFormatter.DISPLAY_FORMAT)
                except ValueError:
                    pass
            
            # If we can't parse it, return empty string
            return ""
            
        except Exception as e:
            print(f"Error converting date to display format: {e}")
            return ""
    
    @staticmethod
    def to_database_format(date_value: Union[str, datetime.date, datetime.datetime, None]) -> str:
        """
        Converts any date format to YYYY-MM-DD for database storage
        
        Args:
            date_value: Date in various formats
            
        Returns:
            str: Date in YYYY-MM-DD format, or empty string if invalid
        """
        if date_value is None:
            return ""
            
        try:
            # If it's already a date or datetime object
            if isinstance(date_value, (datetime.date, datetime.datetime)):
                return date_value.strftime(DateFormatter.ISO_FORMAT)
            
            # If it's a string, try to parse it
            if isinstance(date_value, str):
                date_value = date_value.strip()
                if not date_value:
                    return ""
                
                # Try ISO format first (already in correct format)
                try:
                    parsed_date = datetime.datetime.strptime(date_value, DateFormatter.ISO_FORMAT).date()
                    return parsed_date.strftime(DateFormatter.ISO_FORMAT)
                except ValueError:
                    pass
                
                # Try Argentine format (DD-MM-YYYY)
                try:
                    parsed_date = datetime.datetime.strptime(date_value, DateFormatter.ARGENTINE_FORMAT).date()
                    return parsed_date.strftime(DateFormatter.ISO_FORMAT)
                except ValueError:
                    pass
                
                # Try display format (DD/MM/YYYY)
                try:
                    parsed_date = datetime.datetime.strptime(date_value, DateFormatter.DISPLAY_FORMAT).date()
                    return parsed_date.strftime(DateFormatter.ISO_FORMAT)
                except ValueError:
                    pass
            
            # If we can't parse it, return empty string
            return ""
            
        except Exception as e:
            print(f"Error converting date to database format: {e}")
            return ""
    
    @staticmethod
    def parse_date_input(date_string: str) -> Optional[datetime.date]:
        """
        Parses user input in DD-MM-YYYY or DD/MM/YYYY format
        
        Args:
            date_string: Date string from user input
            
        Returns:
            datetime.date object or None if parsing fails
        """
        if not date_string or not isinstance(date_string, str):
            return None
            
        date_string = date_string.strip()
        if not date_string:
            return None
        
        try:
            # Try Argentine format (DD-MM-YYYY)
            try:
                return datetime.datetime.strptime(date_string, DateFormatter.ARGENTINE_FORMAT).date()
            except ValueError:
                pass
            
            # Try display format (DD/MM/YYYY)
            try:
                return datetime.datetime.strptime(date_string, DateFormatter.DISPLAY_FORMAT).date()
            except ValueError:
                pass
            
            # Try ISO format as fallback (YYYY-MM-DD)
            try:
                return datetime.datetime.strptime(date_string, DateFormatter.ISO_FORMAT).date()
            except ValueError:
                pass
            
            return None
            
        except Exception as e:
            print(f"Error parsing date input '{date_string}': {e}")
            return None
    
    @staticmethod
    def is_date_expired(date_value: Union[str, datetime.date, datetime.datetime], 
                       time_value: Union[str, datetime.time, None] = None) -> bool:
        """
        Determines if a date/time has already passed
        
        Args:
            date_value: Date to check
            time_value: Optional time to check (if None, only checks date)
            
        Returns:
            bool: True if the date/time has passed, False otherwise
        """
        try:
            # Parse the date
            if isinstance(date_value, datetime.datetime):
                check_date = date_value.date()
            elif isinstance(date_value, datetime.date):
                check_date = date_value
            elif isinstance(date_value, str):
                # Try to parse string date
                parsed_date = DateFormatter.parse_date_input(date_value)
                if parsed_date is None:
                    # Try ISO format
                    try:
                        check_date = datetime.datetime.strptime(date_value, DateFormatter.ISO_FORMAT).date()
                    except ValueError:
                        return False  # If we can't parse, assume not expired
                else:
                    check_date = parsed_date
            else:
                return False  # Unknown format, assume not expired
            
            today = datetime.date.today()
            
            # If date is in the future, not expired
            if check_date > today:
                return False
            
            # If date is in the past, expired
            if check_date < today:
                return True
            
            # If date is today, check time if provided
            if time_value is not None:
                try:
                    if isinstance(time_value, datetime.time):
                        check_time = time_value
                    elif isinstance(time_value, str):
                        # Parse time string - try multiple formats
                        time_str = time_value.strip()
                        try:
                            # Try HH:MM:SS format first
                            check_time = datetime.datetime.strptime(time_str, "%H:%M:%S").time()
                        except ValueError:
                            # Try HH:MM format
                            check_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                    else:
                        return False  # Can't parse time, assume not expired
                    
                    # Combine date and time for comparison with 5-minute grace period
                    check_datetime = datetime.datetime.combine(check_date, check_time)
                    now = datetime.datetime.now()
                    
                    # Add 5-minute grace period to avoid issues with synchronization
                    grace_period = datetime.timedelta(minutes=5)
                    check_datetime_with_grace = check_datetime + grace_period
                    
                    return now > check_datetime_with_grace
                    
                except Exception as e:
                    print(f"Error parsing time '{time_value}': {e}")
                    return False  # If time parsing fails, assume not expired
            
            # If no time provided and date is today, not expired
            return False
            
        except Exception as e:
            print(f"Error checking if date is expired: {e}")
            return False  # If anything fails, assume not expired
    
    @staticmethod
    def format_datetime_for_display(dt: Union[datetime.datetime, None]) -> str:
        """
        Formats a datetime object for display in Argentine format
        
        Args:
            dt: datetime object to format
            
        Returns:
            str: Formatted datetime string or empty string if None
        """
        if dt is None:
            return ""
        
        try:
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception as e:
            print(f"Error formatting datetime for display: {e}")
            return ""
    
    @staticmethod
    def get_today_display() -> str:
        """
        Gets today's date in display format
        
        Returns:
            str: Today's date in DD/MM/YYYY format
        """
        return datetime.date.today().strftime(DateFormatter.DISPLAY_FORMAT)
    
    @staticmethod
    def get_today_database() -> str:
        """
        Gets today's date in database format
        
        Returns:
            str: Today's date in YYYY-MM-DD format
        """
        return datetime.date.today().strftime(DateFormatter.ISO_FORMAT)


# Convenience functions for backward compatibility
def to_display_format(date_value):
    """Convenience function for DateFormatter.to_display_format"""
    return DateFormatter.to_display_format(date_value)

def to_database_format(date_value):
    """Convenience function for DateFormatter.to_database_format"""
    return DateFormatter.to_database_format(date_value)

def is_date_expired(date_value, time_value=None):
    """Convenience function for DateFormatter.is_date_expired"""
    return DateFormatter.is_date_expired(date_value, time_value)