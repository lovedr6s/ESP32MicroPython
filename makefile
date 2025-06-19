upload:
	uv run ampy --port /dev/cu.usbserial-0001 put main.py
	uv run rshell -p /dev/cu.usbserial-0001 repl '~ import machine machine.reset()'

screen:
	screen /dev/cu.usbserial-0001 115200