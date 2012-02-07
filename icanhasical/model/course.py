import os
import os.path
import pickle

from datetime import datetime, timedelta
from xml.dom import minidom
from http.client import HTTPConnection

class Error(Exception):
    '''Base class for exceptions in this module.'''
    pass

class InvalidCoursesError(Error):
    '''Exception raised when some of the courses passed to the course loader are
    invalid.
    '''
    def __init__(self, inners):
        self.inners = inners

class CourseError(Error):
    '''Base class for exception related to courses.'''
    def __init__(self, course_sigil):
        self.course_sigil = course_sigil

class NonExistingCourseError(CourseError):
    '''Exception raised when invalid sigils are passed to the course loader'''
    pass

class NonExistingGroupError(CourseError):
    '''Exception raised when a course name is valid but its group number is not'''
    def __init__(self, course_sigil, class_type, group_number):
        super.__init__(course_sigil)
        self.class_type = class_type
        self.group_number = group_number

class Period:
    '''Class that represents a course group continuous period.'''
    _room = ""
    _day = ""
    _starts_at = None
    _ends_at = None
    _parity = "" # "hebdomadaire", "jours impairs", "jours pairs"

class CourseGroup:
    '''Class that represents a specific group for a given course'''
    _sigil = ""
    _title = ""
    _level = "" # "Etude Superieur" or "Baccalaureat"
    _credits = 0
    _weekly_theory = 0.0
    _weekly_labs = 0.0
    _weekly_homework = 0.0
    _department = ""
    _in_charge = ""
    _description = ""
    _note = ""
    _prereqs = ""
    _coreqs = ""
    _documentation = ""
    _website = ""

    _type = "" # "Cours" or "Travaux pratiques"
    _teachers = [] # Possible to have multiple teacher (INF1995)
    _group = 0
    _periods = [] # List of period objects

    @property
    def sigil(self):
        '''Gets the course's sigil'''
        return self._sigil

    @property
    def title(self):
        '''Gets the course's title'''
        return self._title

    @property
    def level(self):
        '''Gets the whether the course is a graduate course or an undergraduate
        one
        '''
        return self._level

    @property
    def credits(self):
        '''Gets the number of credit attributed to the course'''
        return self._credits

    @property
    def weekly_theory(self):
        '''Gets the number of hours spent in theory per week for this course'''
        return self._weekly_theory

    @property
    def type(self):
        '''Gets whether this is a lab or a class'''
        return self._type

    @property
    def group(self):
        '''Gets the group number of this course-group'''
        return self._group

class CourseLoader:
    '''Class responsible of providing course objects'''
    def __init__(self):
        if not os.path.exists(self.CACHE_DIRECTORY):
            os.makedirs(self.CACHE_DIRECTORY, 0o744)
 
    def load(self, *courses):
        '''Returns course object for all the course triplets passed in 
        parameter. If some course strings are invalid, throws an exception
        containing all the errors encountered.
        '''
        course_objects = []
        for i, (sigil, class_type, group) in enumerate(courses):
            try:
                course_objects.append(self._load_course(sigil,
                                                        class_type,
                                                        group))
            except CourseError as excpt:
                # When an exception is catched, only look if other objects are
                # invalid as to return all the errors to the caller, not just
                # the first one
                exceptions = [excpt]
                for course_string in courses[i+1:]:
                    try:
                        self._load_course(sigil, class_type, group)
                    except CourseError as other_exception:
                        exceptions.append(other_exception)
                
                raise InvalidCoursesError(exceptions)
        
        return course_objects  

    def clear_cache(self):
        '''Clears the course cache'''
        filelist = os.listdir(self.CACHE_DIRECTORY)
        for file in filelist:
            os.remove(self.CACHE_DIRECTORY + file)

    def _load_course(self, course_sigil, course_type, course_group):
        '''Load a course object given a course informations. Attemps to load the
        file from the local cache before attempting to download it from the
        web service
        '''
        course_file = self._load_from_cache(course_sigil)
        if (course_file is None):
            course_file = self._load_from_webservice(course_sigil)
            self._cache_file(course_file, course_sigil)

        course_object = self._generate_course_from_xml(course_file,
                                                       course_sigil,
                                                       course_type,
                                                       course_group)
        return course_object

    CACHE_DIRECTORY = "cache/courses/"

    def _load_from_cache(self, course_sigil):
        '''Attemp to load the XML description of a given course from the cache.
        Returns None if the file isn't cached.
        '''
        filepath = self.CACHE_DIRECTORY + course_sigil
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
               return f.read()
        return None

    def _cache_file(self, file, course_sigil):
        '''Save the course object to the cache.'''
        with open(self.CACHE_DIRECTORY + course_sigil, 'w+b') as f:
            f.write(file)

    def _load_from_webservice(self, course_sigil):
        '''Load a course object from the Polytechnique course web service.
        '''
        host = "www.polymtl.ca"
        url = str.format("/etudes/cours/utils/ficheXML.php?sigle={0}",
                         course_sigil)

        connection = HTTPConnection(host)
        connection.request("GET", url, )
        response = connection.getresponse()

        file = response.read()
        connection.close()
        return file

    def _generate_course_from_xml(self, xmlfile, course_sigil, type,
                                  group_number):
        '''Generate the course object from the XML file received from
        Polytechnique's web site.
        '''
        course_dom = minidom.parseString(xmlfile)
        root = course_dom.firstChild

        # The web service returns an xml file containing only one "msg_erreur"
        # tag if the course doesn't exists.
        if root.nodeName == "msg_erreur":
            raise NonExistingCourseError(course_sigil)
        
        # Now check if there is a group of the given type
        type = "Cours" if type == "THEORY" else "Travaux pratiques"
        grouptype_node = None
        for e in root.getElementsByTagName("horaire"):
            if e.getAttribute("type_cours") == type:
                grouptype_node = e

        if grouptype_node is None :
            raise NonExistingGroupError(course_string, type, group_number)

        # And then check if there is a group of that number
        group_node = None
        for e in grouptype_node.getElementsByTagName("groupe_cours"):
            if int(e.getAttribute("no_groupe")) == group_number:
                group_node = e

        if group_node is None :
            raise NonExistingGroupError(course_string, type, group_number)

        # Now that everything has been validated, we can start creating the
        # course object
        course = CourseGroup()
        course._group = group_number
        course._type = type

        self._load_course_details(course,
                                  root.getElementsByTagName("details")[0])
        self._load_group_info(course, group_node)
        return course

    def _load_course_details(self, course, details_node):
        '''Loads course detail from the "detail" node of the xml document'''
        def get_textvalue(tagname):
            '''Returns the text of the first node of a given tag name'''
            nodeList = details_node.getElementsByTagName(tagname)
            if len(nodeList) > 0:
                # There is at least one node with this name
                node = nodeList[0].firstChild
                if (node != None):
                    # The node exist and has text
                    return node.data.strip()
                else:
                    # The node exist but doesn't have text
                    return "";
            else:
                # There is no node with this name
                return None;

        course._sigil = get_textvalue("sigle")
        course._title = get_textvalue("titre")
        course._level = get_textvalue("cycle")
        course._credits = float(get_textvalue("nb_credits"))
        course._weekly_theory = float(get_textvalue("nb_hr_th"))
        course._weekly_labs = float(get_textvalue("nb_hr_lab"))
        course._weekly_homework = float(get_textvalue("nb_hr_pers"))
        course._department = get_textvalue("departement")
        course._in_charge = get_textvalue("responsable")
        course._description = get_textvalue("description")
        course._note = get_textvalue("note")
        course._prereqs = get_textvalue("prerequis")
        course._coreqs = get_textvalue("corequis")
        course._documentation = get_textvalue("documentation")
        course._website = get_textvalue("site_web")

    def _load_group_info(self, course, group_node):
        '''Loads the information relating to the group in the course object'''
        def get_textvalue(node):
            '''Get the text value from a specified node'''
            return node.firstChild.nodeValue.strip()

        # Put teachers in the format "Firstname Lastname". The last child of
        # the "enseignant" node is the first name of the teacher and the first
        # child, the last name.
        course._teachers = ['{0} {1}'.format(get_textvalue(n.lastChild),
                                             get_textvalue(n.firstChild))
                            for n in
                            group_node.getElementsByTagName("enseignant")]

        def contiguous(block1, block2):
            '''Indicates whether two blocks are contiguous'''
            # Period number are in base 16
            periodNumber1 = int(get_textvalue(block1.getElementsByTagName("pernum")[0]), 16)
            periodNumber2 = int(get_textvalue(block2.getElementsByTagName("pernum")[0]), 16)

            room1 = get_textvalue(block1.getElementsByTagName("local")[0])
            room2 = get_textvalue(block2.getElementsByTagName("local")[0])

            if room1 != room2:
                return false

            if periodNumber1 > 0x100:
                # Evening period numbers ends with an extra 0
                return abs(periodNumber1 - periodNumber2) == 0x10
            else :
                return abs(periodNumber1 - periodNumber2) == 1

        # Reverse the list to pop element from it more easily
        block_list = group_node.getElementsByTagName("case_horaire")

        # Group contiguous blocks into sublists (Merci Marchi)
        last_block = None
        grouped_blocks = []
        contiguous_blocks = []

        for current_block in block_list:
            if last_block is not None:
                if contiguous(last_block, current_block):
                    contiguous_blocks.append(current_block)
                else :
                    grouped_blocks.append(contiguous_blocks)
                    contiguous_blocks = [current_block]
            else :
                contiguous_blocks.append(current_block)
            last_block = current_block
        grouped_blocks.append(contiguous_blocks)

        # Create periods from the grouped blocks and append them to the course's
        # period group.
        for group in grouped_blocks:
            period = Period()
            period._room = get_textvalue(group[0].getElementsByTagName("local")[0])
            period._day = get_textvalue(group[0].getElementsByTagName("jour")[0])
            period._parity = get_textvalue(group[0].getElementsByTagName("parite")[0])

            time_string = get_textvalue(group[0].getElementsByTagName("heure")[0])
            period._starts_at = datetime.strptime(time_string, "%HH%M")
            
            # Ends (number of period * 1 hour) later
            period._ends_at = period._starts_at + timedelta(hours = len(group))
            course._periods.append(period)
