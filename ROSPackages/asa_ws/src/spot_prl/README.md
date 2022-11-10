# ROS packages for Holo-Spok (IROS 2022)

## Requirements

### Docker

Spot Core comes with Ubuntu 18.04, which only supports ROS Melodic @ Python 2. However, Boston Dynamics' Python API uses Python 3. We use Docker to avoid compatibility issues such as this one.

### Dependencies

* [catkin_simple](https://github.com/ImperialCollegeLondon/catkin_simple)
* [azure_spatial_anchors_ros](https://github.com/ImperialCollegeLondon/azure_spatial_anchors_ros)

## Installation

Use the Makefile provided:

```
  make .build
  make .catkin_build
```

## Testing

1. Follow the [startup procecure](https://www.youtube.com/watch?v=NiEFDtUhYKA&t=9s)
2. Disconnect from Spot's controller

Using the Makefile provided:

3. Run the ROS interface
```
  make body_driver
```
4. Run the keyboard node
```
  make keyboard
```
5. Now move Spot as prompted by the terminal


## Other repositories used

The following are repositories that we found useful to build our ROS packages:

1. [Clearpath's Spot Ros Driver](https://github.com/clearpathrobotics/spot_ros)
2. [Microsoft's mixed-reality-robot-interaction-demo](https://github.com/microsoft/mixed-reality-robot-interaction-demo)