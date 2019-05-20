import sys
sys.path.insert(0, '/home/forrestli/ITK/build/Wrapping/Generators/Python')
sys.path.insert(1, '/home/forrestli/ITK/build/lib')
sys.path.insert(2, '/home/forrestli/ITKTubeTK/build2/lib')

import itk
import random

from helper2 import Api, rpc

class SegmentApi(Api):
    def __init__(self):
        super().__init__()
        self.segmenter = None
        self.input_image = None
        self.next_tube_id = 0

    @rpc('preprocess')
    def preprocess(self, image, filters):
        filters = {f['filter']:f for f in filters}
        # TODO test if image type is already itk.F, 3
        itk_image = itk.CastImageFilter[type(image), itk.Image[itk.F, 3]].New()(image)
        ImageType = type(itk_image)

        result = itk_image
        if 'median' in filters:
            args = filters['median']
            median_filter = itk.MedianImageFilter[ImageType, ImageType].New()
            median_filter.SetInput(itk_image)
            median_filter.SetRadius(args['radius'])
            median_filter.Update()
            result = median_filter.GetOutput()

        self.persist(result)
        return result

    @rpc('set_segment_image')
    def set_segment_image(self, image):
        if image != self.input_image:
            self.input_image = image
            self.segmenter = itk.TubeTK.SegmentTubes[type(image)].New()
            self.segmenter.SetInputImage(image)

    @rpc('segment')
    def segment(self, position, scale):
        if self.segmenter is None:
            raise Exception('segment image is not set')

        tube = self.segmenter.ExtractTube(position, self.next_tube_id, True)
        if tube is not None:
            self.next_tube_id += 1
            self.persist(tube)
            return tube

    @rpc('delete_tube')
    def delete_tube(self, tube):
        if self.segmenter is None:
            raise Exception('segment image is not set')

        self.segmenter.DeleteTube(tube)
        self.delete(tube)