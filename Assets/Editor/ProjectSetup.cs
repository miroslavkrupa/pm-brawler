using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace PMBrawler.Editor
{
    /// <summary>
    /// First-open convenience: creates Assets/Scenes/Main.unity and registers it for builds.
    /// Adds "PM Brawler" menu items for building and running the WebGL version.
    /// </summary>
    [InitializeOnLoad]
    public static class ProjectSetup
    {
        const string ScenePath = "Assets/Scenes/Main.unity";
        const string WebGLOut = "Builds/WebGL";

        static ProjectSetup()
        {
            EditorApplication.delayCall += () =>
            {
                if (!File.Exists(ScenePath)) CreateMainScene();
            };
        }

        [MenuItem("PM Brawler/Create Main Scene")]
        static void CreateMainScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            // The game builds everything at runtime (GameManager bootstraps itself), so the scene only needs a camera.
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            PlayerSettings.productName = "PM Brawler";
            PlayerSettings.companyName = "PM Brawler";
            Debug.Log("PM Brawler: created " + ScenePath + ". Press Play!");
        }

        [MenuItem("PM Brawler/Build WebGL")]
        static void BuildWebGL()
        {
            if (!File.Exists(ScenePath)) CreateMainScene();
            // GitHub Pages can't send the Content-Encoding headers Unity's compressed builds need
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Disabled;
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = WebGLOut,
                target = BuildTarget.WebGL,
                options = BuildOptions.None
            });
            Debug.Log($"PM Brawler WebGL build: {report.summary.result}, {report.summary.totalSize / (1024 * 1024)} MB → {WebGLOut}");
            if (report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
                EditorUtility.RevealInFinder(WebGLOut);
        }
    }
}
