class ImageCreator:
    fontFile: str
    savePath: str
    convertLength: int

    @classmethod
    def desc(cls):
        return {
            'fontFile': 'resource/style/AdobeHeitiStd-Regular.otf',
            'savePath': 'fileStorage/images',
            'convertLength': 100,
        }
