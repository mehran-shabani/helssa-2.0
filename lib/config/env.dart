class Env {
  static const String apiBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
  static const String buildFlavor =
      String.fromEnvironment('BUILD_FLAVOR', defaultValue: 'dev');
  static const bool analyticsUploadEnabled =
      bool.fromEnvironment('analyticsUploadEnabled', defaultValue: false);
  static const bool kpiPanelEnabled =
      bool.fromEnvironment('kpiPanelEnabled', defaultValue: true);
  static const bool showDevMenu =
      bool.fromEnvironment('showDevMenu', defaultValue: true);
}
