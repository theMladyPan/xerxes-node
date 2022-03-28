#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .unit import Unit

class Pressure(Unit):
    @property
    def mmH2O(self):
        return self.value * 0.10197162129779283

    @property
    def bar(self):
        return self.value * 0.00001

    @property
    def Pascal(self):
        return self.value
    
    @staticmethod
    def from_micro_bar(ubar):
        return Pressure(ubar/10)

    def __repr__(self):
        return f"Pressure({self.value})"

    @property
    def preffered(self):
        return self.Pascal