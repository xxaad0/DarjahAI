from flask import Blueprint, render_template, request,redirect,url_for,flash
from flask_login import login_user, logout_user, login_required, current_user

from .extensions import db

from sqlalchemy.exc  import IntegrityError

from sqlalchemy import text

import pandas as pd

import numpy as np

import math


XPFORTASK=7
GROWTH=1.35

def xp_level_needed(level:int)-> int:
    if level ==1:
        return XPFORTASK
    return math.ceil(XPFORTASK*(GROWTH**(level-1)))

def addXP(character,amount:int,reason:str,XPSTATModel)-> int:
    amount= int(amount)
    if amount<=0:
        return 0
    
    db.session.add(character)
        
    character.xp_total+=amount
    character.xpforlevel+=amount

    levelsGained=0

    while character.xpforlevel>= xp_level_needed(character.level):
        character.xpforlevel-=xp_level_needed(character.level)
        character.level+=1
        levelsGained+=1

    db.session.add(XPSTATModel(c_id=character.id,amount=amount,reason=reason))

            
    return levelsGained