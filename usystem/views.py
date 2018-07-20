# -*- coding: utf-8 -*-
from __future__ import division
from django.shortcuts import render, render_to_response
from usystem.models import models
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.db.models import Q
from operator import and_
from functools import wraps
from django.views.decorators.cache import patch_cache_control
from django.db import transaction
from usystem_master import config
from usystem.forms import *
import base64
from django.db.models import Max, F
import subprocess
from django.core.mail import send_mail
from copy import deepcopy
from django.db.models import Count
from django.db import connection


@transaction.atomic
def connectvnc(request):
    pass

@transaction.atomic
def material(request, num=0):
    pass

@transaction.atomic
def zakaz(request, num=0):
    pass

@transaction.atomic
def print_saw(request, num=0):
    pass

@transaction.atomic
def update_saw(request):
    pass

@transaction.atomic
def index(request):
    return render(request, 'main.html', {})