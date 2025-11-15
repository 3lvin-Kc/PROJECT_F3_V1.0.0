"""
Project Management Module for F3 Platform
==========================================

This module handles all project-related operations including:
- Project creation and initialization
- Project metadata management
- File structure setup
- Database integration
- Project lifecycle management

The project service acts as a bridge between the file system operations
and the database persistence layer.
"""

from .project_service import ProjectService, project_service

__all__ = ['ProjectService', 'project_service']
