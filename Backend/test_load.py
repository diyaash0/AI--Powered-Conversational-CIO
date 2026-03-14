from main import load_enterprise_data

try:
    data = load_enterprise_data()
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
