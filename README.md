##  ASV_WAVE_SIM

<img width="1835" height="884" alt="image" src="https://github.com/user-attachments/assets/c82a63f5-998d-48d2-95f6-dbc0b7a48a4a" />

Kill all servers first

```
# 1. Forcefully kill all simulation and renderer processes with root privileges
sudo pkill -9 -f gz && sudo pkill -9 -f sim && sudo killall -9 ruby

# 2. Wipe the corrupted simulation state and rendering cache
rm -rf ~/.gz/sim/* && rm -rf ~/.gz/rendering/*

# 3. Clear general thumbnail and Gazebo cache
rm -rf ~/.cache/thumbnails/* && rm -rf ~/.cache/gz/*
```

Server

```
source ~/gz_ws/install/setup.bash
export GZ_SIM_RESOURCE_PATH=~/gz_ws/src/asv_wave_sim/gz-waves-models/models:~/gz_ws/src/asv_wave_sim/gz-waves-models/world_models
export GZ_SIM_SYSTEM_PLUGIN_PATH=~/gz_ws/install/lib
# Note: Server doesn't usually need the NVIDIA offload, but it needs the plugin paths.
export GZ_SIM_SYSTEM_PLUGIN_PATH=$GZ_SIM_SYSTEM_PLUGIN_PATH:/home/hsiao/vrx_ws/install/lib
gz sim -v4 -s -r ~/gz_ws/src/asv_wave_sim/gz-waves-models/worlds/waves.sdf
```


Client

```
source ~/gz_ws/install/setup.bash

# Tell Gazebo where your compiled waves plugins are
export GZ_SIM_SYSTEM_PLUGIN_PATH=$GZ_SIM_SYSTEM_PLUGIN_PATH:~/gz_ws/install/lib

# Keep your existing library and rendering exports
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/ros/jazzy/opt/gz_ogre_next_vendor/lib:/opt/ros/jazzy/opt/gz_rendering_vendor/lib
export GZ_RENDERING_BACKEND=ogre2

# Launch with NVIDIA offload
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia gz sim -v4 -g
```

ROS Gazabo Bridge

```
cd ~/gz_ws/
taskset -c 6,7  ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=src/asv_wave_sim/wamv_bridge.yaml
```

## Wind & Wave Adjustment

Try FFT method

```
source ~/gz_ws/install/setup.bash
export GZ_SIM_RESOURCE_PATH=~/gz_ws/src/asv_wave_sim/gz-waves-models/models:~/gz_ws/src/asv_wave_sim/gz-waves-models/world_models
export GZ_SIM_SYSTEM_PLUGIN_PATH=~/gz_ws/install/lib
# Note: Server doesn't usually need the NVIDIA offload, but it needs the plugin paths.
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:/home/hsiao/gz_ws/src/asv_wave_sim/gz-waves-models/world_models
gz sim -v4 -s -r ~/gz_ws/src/asv_wave_sim/gz-waves-models/worlds/waves.sdf
```

Try VRX built-in method

```
source ~/gz_ws/install/setup.bash
export GZ_SIM_RESOURCE_PATH=~/gz_ws/src/asv_wave_sim/gz-waves-models/models:~/gz_ws/src/asv_wave_sim/gz-waves-models/world_models
export GZ_SIM_SYSTEM_PLUGIN_PATH=~/gz_ws/install/lib
# Note: Server doesn't usually need the NVIDIA offload, but it needs the plugin paths.
export GZ_SIM_SYSTEM_PLUGIN_PATH=$GZ_SIM_SYSTEM_PLUGIN_PATH:/home/hsiao/vrx_ws/install/lib
gz sim -v4 -s -r ~/gz_ws/src/asv_wave_sim/gz-waves-models/worlds/waves.sdf
```

## Changes

There are some changes to the plugin SDF schema for hydrodynamics and waves.   

### Waves model and visual plugins

- The `filename` and `name` attributes for the wave model and visal plugins have changed.
- The `<size>` element has been renamed to `<tile_size>` and moved into `<waves>`
- The `<cell_count>` element has been moved into `<waves>`
- Add new element `<algorithm>` to specify the wave generation algorithm. Valid options are: `sinusoid`, `trochoid` and `fft`.
- Add new element `<wind_velocity>` for use with the `fft` algorithm.
- Add new element `<wind_speed>` for use with the `fft` algorithm.
- Add new element `<wind_angle_deg>` for use with the `fft` algorithm.

```xml
<plugin
    filename="gz-waves1-waves-model-system"
    name="gz::sim::systems::WavesModel">
    <static>0</static>
    <update_rate>30</update_rate>
    <wave>
      <!-- Grid dimensions
        - The tile_size and cell_count may be a single value
          for square grids, or a 2d vector if different resolution
          is desired along the x and y axis.
        - The cell_count must be a power of 2 for fft waves
      -->
      <!-- Either: single value for square grids -->
      <tile_size>256.0</tile_size>
      <cell_count>128</cell_count>

      <!-- Or: 2d vectors for different resolution in each axis -->
      <tile_size>256.0 64.0</tile_size>
      <cell_count>128 32</cell_count>

      <!-- Wave algorithms
        - These elements specify the wave generation method
          and wave spectrum parameters.
      -->

      <!-- Either: `fft` waves parameters -->
      <algorithm>fft</algorithm>
      <wind_speed>5.0</wind_speed>
      <wind_angle_deg>135</wind_angle_deg>
      <steepness>2</steepness>

      <!-- Or: `trochoid` waves parameters -->
      <algorithm>trochoid</algorithm>
      <number>3</number>
      <scale>1.5</scale>
      <angle>0.4</angle>
      <amplitude>0.4</amplitude>
      <period>8.0</period>
      <phase>0.0</phase>
      <steepness>1.0</steepness>
      <direction>1 0</direction>
    </wave>
</plugin>
```

The waves visual plugin has the same algorithm elements as the model plugin and extra elements to control the shading algorithm. Two approaches are available:

  - `DYNAMIC_GEOMETRY` uses PBS shaders and is suitable for small areas.
  - `DYNAMIC_TEXTURE` uses a custom shader and is suitable for tiled areas.

```xml
<plugin
    filename="gz-waves1-waves-visual-system"
    name="gz::sim::systems::WavesVisual">
  <static>0</static>

  <!-- set the mesh deformation method  -->
  <mesh_deformation_method>DYNAMIC_GEOMETRY</mesh_deformation_method>

  <!-- number of additional tiles along each axis -->
  <tiles_x>-1 1</tiles_x>
  <tiles_y>-1 1</tiles_y>
  <wave>
    <!-- `fft` wave parameters -->
    <algorithm>fft</algorithm>
    <tile_size>256.0</tile_size>
    <cell_count>128</cell_count>
    <wind_speed>5.0</wind_speed>
    <wind_angle_deg>135</wind_angle_deg>
    <steepness>2</steepness>
  </wave>

  <!--
    Shader parameters only apply when using DYNAMIC_TEXTURE
  -->

  <!-- shader program -->
  <shader language="glsl">
    <vertex>materials/waves_vs.glsl</vertex>
    <fragment>materials/waves_fs.glsl</fragment>
  </shader>
  <shader language="metal">
    <vertex>materials/waves_vs.metal</vertex>
    <fragment>materials/waves_fs.metal</fragment>
  </shader>

  <!-- vertex shader params -->
  <param>
    <shader>vertex</shader>
    <name>world_matrix</name>
  </param>
  <param>
    <shader>vertex</shader>
    <name>worldviewproj_matrix</name>
  </param>
  <param>
    <shader>vertex</shader>
    <name>camera_position</name>
  </param>
  <param>
    <shader>vertex</shader>
    <name>rescale</name>
    <value>0.5</value>
    <type>float</type>
  </param>
  <param>
    <shader>vertex</shader>
    <name>bumpScale</name>
    <value>64 64</value>
    <type>float_array</type>
  </param>
  <param>
    <shader>vertex</shader>
    <name>bumpSpeed</name>
    <value>0.01 0.01</value>
    <type>float_array</type>
  </param>
  <param>
    <shader>vertex</shader>
    <name>t</name>
    <value>TIME</value>
  </param>

  <!-- pixel shader params -->
  <param>
    <shader>fragment</shader>
    <name>deepColor</name>
    <value>0.0 0.05 0.2 1.0</value>
    <type>float_array</type>
  </param>
  <param>
    <shader>fragment</shader>
    <name>shallowColor</name>
    <value>0.0 0.1 0.3 1.0</value>
    <type>float_array</type>
  </param>
  <param>
    <shader>fragment</shader>
    <name>fresnelPower</name>
    <value>5.0</value>
    <type>float</type>
  </param>
  <param>
    <shader>fragment</shader>
    <name>hdrMultiplier</name>
    <value>0.4</value>
    <type>float</type>
  </param>
  <param>
    <shader>fragment</shader>
    <name>bumpMap</name>
    <value>materials/wave_normals.dds</value>
    <type>texture</type>
    <arg>0</arg>
  </param>
  <param>
    <shader>fragment</shader>
    <name>cubeMap</name>
    <value>materials/skybox_lowres.dds</value>
    <type>texture_cube</type>
    <arg>1</arg>
  </param>

</plugin>
```

### Hydrodynamics plugin

- The `filename` and `name` attributes for the hydrodynamics plugin have changed.
- The hydrodynamics parameters are now scoped in an additional `<hydrodynamics>` element.
- The buoyancy and hydrodynamics forces can be applied to specific entities
in a model using the `<enable>` element. The parameter should be a fully
scoped model entity (model, link or collision name).
- The `<wave_model>` element is not used.

```xml
<plugin
  filename="gz-waves1-hydrodynamics-system"
  name="gz::sim::systems::Hydrodynamics">

  <!-- Apply hydrodynamics to the entire model (default) -->
  <enable>model_name</enable>

  <!-- Or apply hydrodynamics to named links -->
  <enable>model_name::link1</enable>
  <enable>model_name::link2</enable>

  <!-- Or apply hydrodynamics to named collisions -->
  <enable>model_name::link1::collision1</enable>
  <enable>model_name::link1::collision2</enable>

  <!-- Hydrodynamics -->
  <hydrodynamics>
    <damping_on>1</damping_on>
    <viscous_drag_on>1</viscous_drag_on>
    <pressure_drag_on>1</pressure_drag_on>

    <!-- Linear and Angular Damping -->  
    <cDampL1>1.0E-6</cDampL1>
    <cDampL2>1.0E-6</cDampL2>
    <cDampR1>1.0E-6</cDampR1>
    <cDampR2>1.0E-6</cDampR2>

    <!-- 'Pressure' Drag -->
    <cPDrag1>1.0E+2</cPDrag1>
    <cPDrag2>1.0E+2</cPDrag2>
    <fPDrag>0.4</fPDrag>
    <cSDrag1>1.0E+2</cSDrag1>
    <cSDrag2>1.0E+2</cSDrag2>
    <fSDrag>0.4</fSDrag>
    <vRDrag>1.0</vRDrag>
  </hydrodynamics>

  <!-- Control visibility of markers -->
  <markers>
    <update_rate>10</update_rate>
    <water_patch>1</water_patch>
    <waterline>1</waterline>
    <underwater_surface>1</underwater_surface>
  </markers>
</plugin>
```

## Tests

```bash
# build with tests
$ colcon build --merge-install --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_MACOSX_RPATH=FALSE -DCMAKE_INSTALL_NAME_DIR=$(pwd)/install/lib -DBUILD_TESTING=ON --packages-select gz-waves1

# run tests
colcon test --merge-install 

# check results
colcon test-result --all --verbose 
```

Testing within a project build directory

```bash
$ cd ~/gz_ws/src/asv_wave_sim/gz-waves
$ mkdir build && cd build
$ cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON
$ make && make test
```

## Plots

Plots may be generated for some of the wave spectra and wave simulation methods:

```bash
./install/bin/PLOT_WaveSpectrum
```

## Legacy versions

There is no plan to back-port new features to Gazebo9 or Gazebo11. The following branches are maintained for legacy support:

- [`gazebo9`](https://github.com/srmainwaring/asv_wave_sim/tree/gazebo9) - for Gazebo9 / ROS Melodic / Ubuntu 18.04 (Bionic).

- [`gazebo11`](https://github.com/srmainwaring/asv_wave_sim/tree/gazebo11) - for Gazebo11 / ROS Noetic / Ubuntu 20.04 (Focal).

In addition there are three branches that contain development iterations of the FFT wave simulation - for Gazebo11 / ROS Noetic / Ubuntu 20.04 (Focal):

- [`feature/fft-waves-v1`](https://github.com/srmainwaring/asv_wave_sim/tree/feature/fft-waves-v1)
- [`feature/fft-waves-v2`](https://github.com/srmainwaring/asv_wave_sim/tree/feature/fft-waves-v2)
- [`feature/fft-waves-v3`](https://github.com/srmainwaring/asv_wave_sim/tree/feature/fft-waves-v3)


## License

This is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the [GNU General Public License](LICENSE) for more details.

This project makes use of other open source software, for full details see the file [LICENSE_THIRDPARTY](LICENSE_THIRDPARTY).

## Acknowledgments

- Jacques Kerner's two part blog describing boat physics for games: [Water interaction model for boats in video games](https://www.gamasutra.com/view/news/237528/Water_interaction_model_for_boats_in_video_games.php) and [Water interaction model for boats in video games: Part 2](https://www.gamasutra.com/view/news/263237/Water_interaction_model_for_boats_in_video_games_Part_2.php).
- The [CGAL](https://doc.cgal.org) libraries are used for the wave field and model meshes.
- The [UUV Simulator](https://github.com/uuvsimulator/uuv_simulator) package for the orginal vertex shaders used in the wave field visuals.
- The [VMRC](https://bitbucket.org/osrf/vmrc) package for textures and meshes used in the wave field visuals.
- Jerry Tessendorf's paper on	[Simulating Ocean Water](https://people.cs.clemson.edu/~jtessen/reports/papers_files/coursenotes2004.pdf)
- Curtis Mobley's web book [Ocean Optics](https://www.oceanopticsbook.info/) in particular the section on [Modeling Sea Surfaces](https://www.oceanopticsbook.info/view/surfaces/level-2/modeling-sea-surfaces) and [example IDL code](https://www.oceanopticsbook.info/packages/iws_l2h/conversion/files/IDL-SurfaceGenerationCode.zip)  
