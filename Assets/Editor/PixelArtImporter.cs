using UnityEditor;
using UnityEngine;

namespace PMBrawler.Editor
{
    /// <summary>
    /// Imports Resources/Art as crisp, uncompressed pixel art and Resources/ArtHD (hand-drawn) as smooth,
    /// mipmapped, compressed textures so the bigger images stay light in the web build.
    /// </summary>
    public class PixelArtImporter : AssetPostprocessor
    {
        void OnPreprocessTexture()
        {
            bool pixel = assetPath.StartsWith("Assets/Resources/Art/");
            bool hd = assetPath.StartsWith("Assets/Resources/ArtHD/");
            if (!pixel && !hd) return;
            var ti = (TextureImporter)assetImporter;
            ti.textureType = TextureImporterType.Default;
            ti.alphaIsTransparency = true;
            ti.wrapMode = TextureWrapMode.Clamp;
            ti.npotScale = TextureImporterNPOTScale.None;
            if (pixel)
            {
                ti.mipmapEnabled = false;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.maxTextureSize = 4096;
            }
            else
            {
                ti.mipmapEnabled = true;            // thin ink lines would shimmer when scaled down without them
                ti.filterMode = FilterMode.Trilinear;
                ti.textureCompression = TextureImporterCompression.Compressed;
                ti.crunchedCompression = true;      // much smaller download
                ti.compressionQuality = 75;
                ti.maxTextureSize = 4096;
            }
        }
    }
}
