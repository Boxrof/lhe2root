import re
import os
import functools
import numpy as np
#https://docs.python.org/dev/library/functools.html#functools.cached_property

class lhe_reader(object):
    def __init__(self, lhefile) -> None:
        """A class to read LHE files and perform cursory operations like 
        cutting down to size and checking equality

        Parameters
        ----------
        lhefile : str
            the .lhe file you are using

        Raises
        ------
        FileNotFoundError
            Filename should have the .lhe extension
        """
        if lhefile.split('.')[-1] != 'lhe':
            raise FileNotFoundError("LHE File Extension Required!")
        
        self.lhefile = os.path.abspath(lhefile)
        self.event_selection_regex = re.compile(r'(?s)(<event>(.*?)</event>)') #regular expression to find every event
        with open(self.lhefile) as f:
            self.text = f.read()
        
    @functools.cached_property 
    def cross_section(self):
        """Gets the cross section and its uncertainty using regular expressions

        Returns
        -------
        Tuple[str, str]
            A tuple of strings containing the cross section and its uncertainty
        """
        
        cross_section = uncertainty = ""
        
        # with open(self.lhefile) as getting_cross_section:
        head = self.non_event_portions[0] #The part before the events contains the cross section
        
        #This regex was made by the very very helpful https://pythex.org/ (shoutout professor Upsorn Praphamontripong)
        cross_finder = re.compile(r'<init>\n.+\n.+(\d+\.\d+E(\+|-)\d{2})\s+(\d+\.\d+E(\+|-)\d{2})\s+(\d+\.\d+E(\+|-)\d{2})(\d|\s)+</init>')
        cross_section_match = re.search(cross_finder,head)
        
        cross_section = cross_section_match.group(1)
        
        uncertainty = cross_section_match.group(3)
        
        return float(cross_section), float(uncertainty) #returns the cross section and its uncertainty
    
    @functools.cached_property 
    def all_events(self):
        """This function opens and collects every LHE event and puts them in a list to return
        stores the attribute as a cached property
        Returns
        -------
        list[str]
            A list of every event sequence as strings from the file (AKA everything between <event> and </event>)
        """
        all_matches = re.findall(self.event_selection_regex, self.text)
        all_matches = [item[0] for item in all_matches]
        return all_matches
    
    @functools.cached_property
    def num_events(self):
        """Returns the number of events in the file as a cached property

        Returns
        -------
        int
            The number of events in the LHE file
        """
        return len(self.all_events)
        
    @functools.cached_property
    def non_event_portions(self):
        """This function gets everything in an LHE file that is not an event 
        (everything before the first <event> and everything after the last </event>)

        Returns
        -------
        Tuple[str, str]
            Two strings of everything before the first <event> and everything after the last </event>
        """
        f_start = self.text[:self.text.find("<event>")] #everything until the first event
        f_end = self.text[self.text.rfind("</event>") + len("</event>"):] #everything after the last event
        return f_start, f_end

    def __eq__(self, __o: object) -> bool:
        """Defines a metric for equality between two LHE files

        Parameters
        ----------
        __o : object
            Some other object - only useful if it's another LHE_reader class

        Returns
        -------
        bool
            Whether the events are the same
        """
        if isinstance(__o, lhe_reader):
            if self.all_events == __o.all_events:
                return True
        
        return False
    
    def __str__(self) -> str:
        """Function toString that displays the number of events and the cross section of an LHE file

        Returns
        -------
        str
            the string representation of the class
        """
        to_str = ""
        to_str += "LHE file " + self.lhefile
        to_str += "\n\tN: " + str(self.num_events)
        to_str += "\n\t\u03C3: " + "{:e}".format(self.cross_section[0]) + "\n"
        return to_str

    def cut_down_to_size(self, n, verbose=False, shuffled=False):
        """Cuts the number of events in an LHE file down to n events while preserving other aspects of the file

        Parameters
        ----------
        n : int
            The number of events you want to keep
        verbose : bool, optional
            Whether you want the function to be verbose, by default False
        shuffled : bool, optional
            Whether you want the lhe files to be shuffled before sampling them

        Returns
        -------
        str
            A string that should be passed to a file of the LHE file

        Raises
        ------
        ValueError
            n must be <= the number of events in the file
        ValueError
            n must be > 0
        """
        start_of_file, end_of_file = self.non_event_portions
        
        orig_num = len(self.all_events)
        
        n = int(n)
        
        if n == orig_num:
            return start_of_file + ("\n".join(self.all_events)) + end_of_file
        elif n > orig_num:
            raise ValueError("n must be less than or equal to the number of events already in the file!")
        elif n == 0:
            raise ValueError("Selecting 0 events makes literally no sense")
        if verbose:
            print(orig_num, "events ->", n, "events")
        
        cut_down = np.random.choice(self.all_events, n) if shuffled else self.all_events[:n]

        
        return start_of_file + ("\n".join(cut_down)) + end_of_file #this would ideally be placed directly into a file