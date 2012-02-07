import re

def parse(course_string):
    '''Parses a course string and returns the associated (sigil, type, group)
    triplet
    '''
    match = re.match(r"(\w+)-([lt])(\d+)", course_string)
    if match is None:
        raise ValueError("Invalid course string")
    (sigil, class_type, group) = match.groups()
    class_type = "THEORY" if class_type == 't' else "LAB"
    group = int(group)
    return (sigil, class_type, group)