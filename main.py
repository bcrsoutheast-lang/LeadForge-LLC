from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client
from datetime import datetime
