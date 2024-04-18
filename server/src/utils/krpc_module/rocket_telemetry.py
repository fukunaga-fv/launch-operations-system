from .base_rocket import BaseRocket
from .rocket_stage import RocketStage


class RocketTelemetry(BaseRocket):
    def __init__(self,krpc_connect_server_name:str) -> None:
        """initializer"""
        super().__init__(krpc_connect_server_name)
        self.initialize_stages()

    def initialize_stages(self) -> None:
        """宇宙船のステージを初期化する"""
        self.satellite_bus = RocketStage(self.find_parts_by_tag("satellite_bus"))
        self.first_stage = RocketStage(self.find_parts_by_tag("first_stage"))
        self.second_stage = RocketStage(self.find_parts_by_tag("second_stage"))
        self.launch_clamps = RocketStage(self.find_parts_by_tag("launch_clamp"))

    def get_all_engines_status(self):
        """宇宙船のすべてのエンジンの基本ステータス情報を取得する

        Documents:
            https://krpc.github.io/krpc/python/api/space-center/parts.html#SpaceCenter.Engine

        Returns:
            list[dict]: すべてのエンジンのステータス情報を含むリスト
                dict:
                - tag (str): エンジンパーツに関連付けられたタグ
                - stage (int): エンジンのステージ番号
                - name (str): エンジンパーツの名前
                - active (bool): エンジンが現在アクティブかどうかを示すブール値
                - thrust (float): エンジンの現在の推力（ニュートン単位）
                - available_thrust (float): 現在利用可能な推力
                - available_thrust_at (float): 現在の大気圧における利用可能な推力
                - max_thrust (float): エンジンの最大推力
                - max_thrust_at (float): 現在の大気圧での最大推力
                - max_vacuum_thrust (float): 真空中での最大推力
                - thrust_limit (float): 推力制限（パーセンテージ）
                - isp (float): エンジンの比推力
                - specific_impulse_at (float): 現在の大気圧での比推力
                - vacuum_specific_impulse (float): 真空中の比推力
                - propellant_names (list[str]): 使用する推進剤の名前
                - propellant_ratios (dict[str, float]): 推進剤の比率
                - propellants (List[Propellant]): エンジンに使用される推進剤の詳細
                - throttle (float): 現在のスロットル位置（パーセンテージ）
                - temperature (float): パーツの現在の温度
                - max_temperature (float): パーツの最大許容温度
                - skin_temperature (float): パーツの表面温度
                - max_skin_temperature (float): パーツの表面の最大許容温度
        """
        engines_status = []  # すべてのエンジンのステータス情報を保持するリスト

        for engine in self.vessel.parts.engines:
            current_pressure = self.vessel.flight().static_pressure  # 現在の大気圧（パスカル）
            # パスカルからアトモスフィアに変換（1アトモスフィア = 101325 パスカル）
            current_pressure_atm = current_pressure / 101325

            status = {
                "tag": engine.part.tag,
                "stage": engine.part.stage,
                "name": engine.part.name,
                "active": engine.active,
                "thrust": engine.thrust,
                "available_thrust": engine.available_thrust,
                "available_thrust_at": engine.available_thrust_at(pressure=current_pressure_atm),
                "max_thrust": engine.max_thrust,
                "max_thrust_at": engine.max_thrust_at(pressure=current_pressure_atm),
                "max_vacuum_thrust": engine.max_vacuum_thrust,
                "thrust_limit": engine.thrust_limit,
                "isp": engine.specific_impulse,
                "specific_impulse_at": engine.specific_impulse_at(pressure=current_pressure_atm),
                "vacuum_specific_impulse": engine.vacuum_specific_impulse,
                "propellant_names": engine.propellant_names,
                "propellant_ratios": engine.propellant_ratios,
                # ref: https://krpc.github.io/krpc/python/api/space-center/parts.html#SpaceCenter.Propellant
                "propellants": engine.propellants,
                "throttle": engine.throttle,
                "temperature": engine.part.temperature,
                "max_temperature": engine.part.max_temperature,
                "skin_temperature": engine.part.skin_temperature,
                "max_skin_temperature": engine.part.max_skin_temperature,
            }
            engines_status.append(status)
        return engines_status

    def get_atmosphere_info(self):
        """宇宙船の現在位置での大気情報を取得する

        Returns:
            dict:
            - angle_of_attack (float): 攻撃角
            - sideslip_angle (float): 横滑り角
            - mach (float): マッハ数
            - dynamic_pressure (float): 動的圧力
            - atmosphere_density (float): 大気密度
            - atmospheric_pressure (float): 大気圧
            - atmospheric_drag (float): 大気抵抗加速度（自己計算）
            - terminal_velocity (float): 終端速度
        """
        flight_info = self.vessel.flight(self.reference_frame)
        return {
            "angle_of_attack": flight_info.angle_of_attack,
            "sideslip_angle": flight_info.sideslip_angle,
            "mach": flight_info.mach,
            "dynamic_pressure": flight_info.dynamic_pressure,
            "atmosphere_density": flight_info.atmosphere_density,
            "atmospheric_pressure": flight_info.static_pressure,
            "atmospheric_drag": self.calculate_atmospheric_drag_acceleration(),
            "terminal_velocity": flight_info.terminal_velocity,
        }

    def get_orbit_info(self):
        """
        宇宙船の軌道に関する情報を取得する

        Returns:
            dict:
            - orbital_speed (float): 軌道速度
            - apoapsis_altitude (float): アポアプシス（遠地点）の高度
            - periapsis_altitude (float): ペリアプシス（近地点）の高度
            - period (float): 軌道周期
            - time_to_apoapsis (float): アポアプシス（遠地点）までの時間
            - time_to_periapsis (float): ペリアプシス（近地点）までの時間
            - semi_major_axis (float): 長半径
            - inclination (float): 軌道傾斜角
            - eccentricity (float): 軌道離心率
            - longitude_of_ascending_node (float): 昇交点の経度
            - argument_of_periapsis (float): 近点引数
            - prograde (float): 前進方向のベクトル
        """
        orbit = self.vessel.orbit
        flight_info = self.vessel.flight(self.reference_frame)

        return {
            "orbital_speed": orbit.speed,
            "apoapsis_altitude": orbit.apoapsis_altitude,
            "periapsis_altitude": orbit.periapsis_altitude,
            "period": orbit.period,
            "time_to_apoapsis": orbit.time_to_apoapsis,
            "time_to_periapsis": orbit.time_to_periapsis,
            "semi_major_axis": orbit.semi_major_axis,
            "inclination": orbit.inclination,
            "eccentricity": orbit.eccentricity,
            "longitude_of_ascending_node": orbit.longitude_of_ascending_node,
            "argument_of_periapsis": orbit.argument_of_periapsis,
            "prograde": flight_info.prograde,
        }

    def get_surface_info(self):
        """
        宇宙船が現在接触している表面の情報を取得する

        Returns:
            dict:
            - altitude_als (float): 平均海面高度
            - altitude_true (float): 実際の表面高度
            - pitch (float): ピッチ角
            - heading (float): 進行方向
            - roll (float): ロール角
            - surface_speed (float): 表面速度
            - vertical_speed (float): 垂直速度
            - surface_horizontal_speed (float): 水平面速度
            - latitude (float): 緯度
            - longitude (float): 経度
            - biome (str): バイオーム
            - situation (VesselSituation): 宇宙船の状況
        """
        flight_info = self.vessel.flight(self.reference_frame)
        return {
            "altitude_als": flight_info.mean_altitude,
            "altitude_true": flight_info.surface_altitude,
            "pitch": flight_info.pitch,
            "heading": flight_info.heading,
            "roll": flight_info.roll,
            "surface_speed": flight_info.speed,
            "vertical_speed": flight_info.vertical_speed,
            "surface_horizontal_speed": flight_info.horizontal_speed,
            "latitude": flight_info.latitude,
            "longitude": flight_info.longitude,
            "biome": self.vessel.biome,
            "situation": self.vessel.situation,
        }

    def get_delta_v_status(self):
        """
        ロケットのデルタVステータスを返す

        Returns:
        - stage_delta_v_atom (float): 最後のステージの大気中でのデルタV
        - stage_delta_v_vac (float): 最後のステージの真空中でのデルタV
        - total_delta_v_atom (float): 全ステージの大気中での合計デルタV
        - total_delta_v_vac (float): 全ステージの真空中での合計デルタV
        - delta_v_list (list[dict]): 各エンジンごとのデルタV計算結果を含むリスト
            dict:
            - stage (int): エンジンのステージ番号
            - start_mass (float): ステージ開始時の質量
            - end_mass (float): ステージ終了時の質量
            - burned_mass (float): 燃焼した燃料の質量
            - max_thrust (float): 最大真空推力
            - twr (float): 推力重量比（真空中）
            - slt (float): 海面推力重量比
            - isp (float): 大気中での比推力
            - atom_delta_v (float): 大気中でのデルタV
            - vac_delta_v (float): 真空中でのデルタV
            - time (float): 燃焼時間
        """
        payload_mass = self.satellite_bus.mass
        first_stage_mass = self.first_stage.mass
        second_stage_mass = self.second_stage.mass

        stages_start_mass = [
            payload_mass + first_stage_mass,  # 第1ステージのスタート質量
            payload_mass + first_stage_mass + second_stage_mass,  # 第2ステージのスタート質量
        ]

        engines = self.get_all_engines_status()

        delta_v_list = []

        for i, engine in enumerate(engines):
            start_mass = stages_start_mass[min(i, len(stages_start_mass) - 1)]
            max_vac_thrust = engine["max_vacuum_thrust"]
            max_thrust = engine["max_thrust"]
            fuel_mass = sum(propellant.total_resource_available for propellant in engine["propellants"])
            vac_isp = engine["vacuum_specific_impulse"]
            atom_isp = engine["specific_impulse_at"]
            slt = max_thrust / (start_mass * 9.81)
            twr = max_vac_thrust / (start_mass * 9.81)
            vac_delta_v = self.calculate_delta_v(vac_isp, fuel_mass, start_mass)
            atom_delta_v = self.calculate_delta_v(atom_isp, fuel_mass, start_mass)
            burn_time = self.burn_time_estimation(atom_isp, fuel_mass, max_thrust)
            end_mass = start_mass - fuel_mass

            delta_v_list.append(
                {
                    "stage": engine["stage"],
                    "start_mass": start_mass,
                    "end_mass": end_mass,
                    "burned_mass": fuel_mass,
                    "max_thrust": max_vac_thrust,
                    "twr": twr,
                    "slt": slt,
                    "isp": atom_isp,
                    "atom_delta_v": atom_delta_v,
                    "vac_delta_v": vac_delta_v,
                    "time": burn_time,
                }
            )

        # Calculate the total delta V for atom and vac
        total_delta_v_atom = sum([stage["atom_delta_v"] for stage in delta_v_list])
        total_delta_v_vac = sum([stage["vac_delta_v"] for stage in delta_v_list])

        # Calculate the stage delta V for atom and vac
        stage_delta_v_atom = delta_v_list[-1]["atom_delta_v"] if delta_v_list else 0
        stage_delta_v_vac = delta_v_list[-1]["vac_delta_v"] if delta_v_list else 0

        return {
            "stage_delta_v_atom": stage_delta_v_atom,
            "stage_delta_v_vac": stage_delta_v_vac,
            "total_delta_v_atom": total_delta_v_atom,
            "total_delta_v_vac": total_delta_v_vac,
            "delta_v_list": delta_v_list,
        }

    def get_thermal_status(self):
        """ロケット各ステージの熱関連データを返す

        Returns:
        - satellite_bus (dict): 人工衛星の熱データ
        - first_stage (dict): 第一段ロケットの熱データ
        - second_stage (dict): 第二段ロケットの熱データ
            dict:
            - tag (str): パーツに割り当てられたタグ
            - name (str): パーツの名前
            - title (str): パーツのタイトル
            - temperature (float): パーツの現在の温度
            - max_temperature (float): パーツの最大許容温度
            - skin_temperature (float): パーツの表皮温度
            - max_skin_temperature (float): パーツの表皮の最大許容温度
            - thermal_percentage (float): パーツの温度が最大許容温度に対してどの程度の割合であるかをパーセントで表示
        """
        return {
            "satellite_bus": self.satellite_bus.get_thermal_data(),
            "first_stage": self.first_stage.get_thermal_data(),
            "second_stage": self.second_stage.get_thermal_data(),
        }

    def get_satellite_bus_status(self):
        """サテライトバスに属する各構成パーツのステータスを返す

        Returns:
            dict:
            - name (str): パーツの名前
            - title (str): パーツのタイトル
            - shielded (bool): パーツがシールドされているかどうか
            - temperature (float): パーツの現在の温度
            - max_temperature (float): パーツの最大許容温度
            - skin_temperature (float): パーツの表皮温度
            - max_skin_temperature (float): パーツの表皮の最大許容温度
            - thermal_percentage (float): パーツの現在の温度が最大許容温度の何パーセントか
            - current_charge (float): パーツに蓄積されている電力の現在量（「ElectricCharge」が存在する場合）
            - max_charge (float): パーツに蓄積可能な電力の最大量（「ElectricCharge」が存在する場合）

        パーツが存在しない場合はエラーメッセージを含む辞書を返す。
        """
        parts_info = []
        for part in self.satellite_bus.parts:
            part_info = {
                "name": part.name,
                "title": part.title,
                "shielded": part.shielded,
                "temperature": part.temperature,
                "max_temperature": part.max_temperature,
                "skin_temperature": part.skin_temperature,
                "max_skin_temperature": part.max_skin_temperature,
                "thermal_percentage": part.temperature / part.max_temperature * 100 if part.max_temperature else 0,
                "current_charge": part.resources.amount("ElectricCharge") if "ElectricCharge" in part.resources.names else 0,
                "max_charge": part.resources.max("ElectricCharge") if "ElectricCharge" in part.resources.names else 0,
            }
            parts_info.append(part_info)

        return parts_info if parts_info else {"error": "Parts not found"}

    def get_communication_status(self):
        """宇宙船の通信システムの状態を取得する

        Documents:
            https://krpc.github.io/krpc/python/api/space-center/comms.html#SpaceCenter.Comms

        Returns:
            - can_communicate (bool): 宇宙船が通信可能かどうかのブール値
            - can_transmit_science (bool): 科学データを送信できるかどうかのブール値
            - signal_strength (float): 現在の信号強度
            - signal_delay (float): 信号遅延時間
            - total_comm_power (float): 通信システムの合計電力
            - control_path (list[dict]): 通信経路に関する情報のリスト
                dict:
                - type (str): リンクタイプ（'home', 'control', 'relay'）
                - signal_strength (float): リンクの信号強度

        """
        comm = self.vessel.comms
        control_path_info = []
        for link in comm.control_path:
            link_info = {
                "type": link.type.name,
                "signal_strength": link.signal_strength,
            }
            control_path_info.append(link_info)

        return {
            "can_communicate": comm.can_communicate,
            "can_transmit_science": comm.can_transmit_science,
            "signal_strength": comm.signal_strength,
            "signal_delay": comm.signal_delay,
            "total_comm_power": comm.power,
            "control_path": control_path_info,
        }
