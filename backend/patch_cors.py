import sys
import os

print("Analyzing main.py...")

try:
    with open("main.py", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1. Check if CORS is already there
    if any("CORSMiddleware" in line for line in lines):
        print("✅ CORS is already configured. No changes needed.")
        sys.exit()

    new_lines = []
    import_added = False
    middleware_added = False

    for line in lines:
        # 2. Add the Import statement near the top
        if not import_added and (line.startswith("from") or line.startswith("import")):
            new_lines.append("from fastapi.middleware.cors import CORSMiddleware\n")
            import_added = True
        
        new_lines.append(line)

        # 3. Add the Middleware configuration right after "app = FastAPI()"
        if not middleware_added and "app = FastAPI()" in line:
            new_lines.append('\n# --- CORS CONFIGURATION (Added via Patch) ---\n')
            new_lines.append('origins = ["http://localhost:3000", "http://127.0.0.1:3000"]\n')
            new_lines.append('app.add_middleware(\n')
            new_lines.append('    CORSMiddleware,\n')
            new_lines.append('    allow_origins=origins,\n')
            new_lines.append('    allow_credentials=True,\n')
            new_lines.append('    allow_methods=["*"],\n')
            new_lines.append('    allow_headers=["*"],\n')
            new_lines.append(')\n')
            new_lines.append('# ------------------------------------------\n')
            middleware_added = True

    # 4. Save the changes back
    with open("main.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("✅ Success! CORSMiddleware has been added to main.py")

except FileNotFoundError:
    print("❌ Error: Could not find main.py. Make sure you are in the 'backend' folder.")
