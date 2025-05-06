import os
import sys
import json
from random import randint
sys.path.append(os.path.abspath(os.path.join(__file__, *[os.pardir] * 3)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'simplelms.settings'
import django
django.setup()

import csv
from django.contrib.auth.models import User
from core.models import Course, CourseMember, Comment, CourseContent

course_dict = {c.pk: c for c in Course.objects.all()}
content_dict = {c.pk: c for c in CourseContent.objects.all()}
user_dict = {u.pk: u for u in User.objects.all()}

with open('./csv_data/user-data.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for num, row in enumerate(reader):
            if not User.objects.filter(username=row['username']).exists():
                User.objects.create_user(
					 id=num+2, username=row['username'], 
					 password=row['password'], 
					 email=row['email'])
    
with open('./csv_data/course-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for num,row in enumerate(reader):           
        if not Course.objects.filter(pk=num+1).exists():
            # Map teacher ID to a valid user ID (between 2 and 51)
            teacher_id = int(row['teacher'])
            if teacher_id > 50:
                teacher_id = randint(2, 50)
            elif teacher_id < 2:
                teacher_id = 2
                        
            Course.objects.create(
					id=num+1, name=row['name'], 
					description=row['description'], 
					price=row['price'],
					teacher=User.objects.get(pk=teacher_id))
            
with open('csv_data/member-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for num, row in enumerate(reader):
        if not CourseMember.objects.filter(pk=num+1).exists():
            CourseMember.objects.create(
		            course_id=Course.objects.get(pk=int(row['course_id'])),
					user_id=User.objects.get(pk=int(row['user_id'])),
					id=num+1, roles=row['roles'])
            
with open('csv_data/contents.json') as jsonfile:
    contents = json.load(jsonfile)
    obj_create = []
    for num, row in enumerate(contents, start=1):  # Start enumeration from 1
        if num not in content_dict:  # Check if this ID is not already used
            # Map course ID to a valid course ID
            course_id = int(row['course_id'])
            if course_id > len(course_dict):
                course_id = randint(1, len(course_dict))
            elif course_id < 1:
                course_id = 1
                
            obj_create.append(CourseContent(
                id=num,  # Use the enumeration number as ID
                course_id=course_dict.get(course_id),
                video_url=row['video_url'],
                name=row['name'],
                description=row['description']
            ))
    CourseContent.objects.bulk_create(obj_create)

# Refresh content_dict
content_dict = {c.pk: c for c in CourseContent.objects.all()}

# Create a dictionary to track course members
member_dict = {}  # key: (user_id, course_id), value: member

with open('csv_data/comments.json') as jsonfile:
    comments = json.load(jsonfile)
    obj_create = []
    for row in comments:
        # Map user ID to a valid user ID (between 2 and 51)
        uid = int(row['user_id'])
        if uid > 50:
            uid = randint(2, 50)
        elif uid < 2:
            uid = 2
            
        # Map content ID to a valid content ID
        content_id = int(row['content_id'])
        if content_id > len(content_dict):
            content_id = randint(1, len(content_dict))
        elif content_id < 1:
            content_id = 1
            
        if content_id in content_dict and uid in user_dict:
            # First, get or create a CourseMember for this user
            course = content_dict[content_id].course_id
            
            # Check if we already have a member for this user and course
            member_key = (uid, course.id)
            if member_key not in member_dict:
                # Get the next available ID
                last_member = CourseMember.objects.order_by('-id').first()
                next_id = (last_member.id + 1) if last_member else 1
                
                # Create new course member
                member = CourseMember.objects.create(
                    id=next_id,
                    user_id=user_dict[uid],
                    course_id=course,
                    roles='std'
                )
                member_dict[member_key] = member
            
            obj_create.append(Comment(
                content_id=content_dict[content_id],
                member_id=member_dict[member_key],
                comment=row['comment']
            ))
    Comment.objects.bulk_create(obj_create)