import asyncio
from kasa import SmartPlug

async def control_plug(ip, action):
    plug = SmartPlug(ip)
    try:
        await plug.update()
        if action == "on":
            await plug.turn_on()
            print("Plug turned ON!")
        elif action == "off":
            await plug.turn_off()
            print("Plug turned OFF!")
        else:
            print("Invalid action. Use 'on' or 'off'.")
    except Exception as e:
        print(f"Error: {e}")
        print("Retrying...")
        await asyncio.sleep(1)
        await control_plug(ip, action)

# Replace with the correct IP and desired action
asyncio.run(control_plug("192.168.40.176", "on"))
