import troposphere.robomaker as robomaker

print("Bug 1: AWSObject subclasses require undocumented 'title' parameter")
print("=" * 60)

try:
    fleet = robomaker.Fleet(Name='TestFleet')
    print("Created Fleet without title - UNEXPECTED SUCCESS")
except TypeError as e:
    print(f"Fleet() without title fails: {e}")

fleet_with_title = robomaker.Fleet('MyFleet', Name='TestFleet')
print(f"Fleet() with title works: {fleet_with_title.to_dict()}")

print("\n" + "=" * 60)
print("Bug 2: Same issue with all AWSObject subclasses")

try:
    robot = robomaker.Robot(
        Architecture='X86_64',
        GreengrassGroupId='test-group'
    )
except TypeError as e:
    print(f"Robot() without title fails: {e}")

try:
    app = robomaker.SimulationApplication(
        RobotSoftwareSuite=robomaker.RobotSoftwareSuite(Name='ROS'),
        SimulationSoftwareSuite=robomaker.SimulationSoftwareSuite(Name='Gazebo')
    )
except TypeError as e:
    print(f"SimulationApplication() without title fails: {e}")

print("\n" + "=" * 60)
print("Bug 3: Inconsistency - AWSProperty subclasses don't need title")

suite = robomaker.RobotSoftwareSuite(Name='ROS')
print(f"RobotSoftwareSuite (AWSProperty) works without title: {suite.to_dict()}")

print("\n" + "=" * 60)
print("API Contract Violation: The 'title' parameter is:")
print("1. Not documented in the module")
print("2. Not shown in props")
print("3. Marked as Optional[str] in signature but actually required")
print("4. Inconsistent between AWSObject and AWSProperty subclasses")