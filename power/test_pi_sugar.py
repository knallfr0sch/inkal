from power.pi_sugar import PiSugar


def test_get_battery():
    pi_sugar = PiSugar()
    battery_level = pi_sugar.get_battery()
    print(battery_level)
    assert battery_level >= 0.0 and battery_level <= 1.0
