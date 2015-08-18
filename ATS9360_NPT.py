# ATS9360_NPT.py driver for The aquisition board Alzar ATS9360
# Etienne Dumur <etienne.dumur@neel.cnrs.fr> 2015
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
import types
import visa
import time
import multiprocessing as mp
from ATS9360 import atsapi as ats
from ATS9360 import sub_process_2 as sub_process
from ATS9360 import data_treatment
import numpy as np

class ATS9360_NPT(Instrument):

    def __init__(self, name, address=None):
        Instrument.__init__(self, name, tags=['measure'])

        self.add_parameter('clock_source',
            type        = types.StringType,
            flags       = Instrument.FLAG_GETSET,
            option_list = ('internal', 'external')
            )

        self.add_parameter('clock_edge',
            type        = types.StringType,
            flags       = Instrument.FLAG_GETSET,
            option_list = ('rising', 'falling'),
            )

        self.add_parameter('samplerate',
            type        = types.FloatType ,
            flags       = Instrument.FLAG_GETSET,
            units       = 'MS/s'
            )

        self.add_parameter('trigger_range',
            type        = types.FloatType ,
            flags       = Instrument.FLAG_GETSET,
            option_list = (5., 2.5, 1.),
            units       = 'V'
            )

        self.add_parameter('trigger_level',
            type        = types.FloatType ,
            flags       = Instrument.FLAG_GETSET,
            units       = 'V'
            )

        self.add_parameter('trigger_delay',
            type        = types.FloatType ,
            flags       = Instrument.FLAG_GETSET,
            units       = 'ns'
            )

        self.add_parameter('trigger_slope',
            type        = types.StringType ,
            flags       = Instrument.FLAG_GETSET,
            option_list = ('positive', 'negative')
            )

        self.add_parameter('acquisition_time',
            type        = types.FloatType,
            flags       = Instrument.FLAG_GET_AFTER_SET | Instrument.FLAG_GETSET,
            units       = 'ns'
            )

        self.add_parameter('acquired_samples',
            type        = types.IntType,
            flags       = Instrument.FLAG_GET,
            units       = 'S'
            )

        self.add_parameter('buffers_per_acquisition',
            type        = types.IntType,
            flags       = Instrument.FLAG_GETSET,
            )

        self.add_parameter('records_per_buffer',
            type        = types.IntType,
            flags       = Instrument.FLAG_GETSET,
            )

        self.add_parameter('nb_buffer_allocated',
            type        = types.IntType,
            flags       = Instrument.FLAG_GETSET,
            )

        self.add_parameter('nb_process_data_treatment',
            type        = types.IntType,
            flags       = Instrument.FLAG_GETSET,
            )


        self.allow_samplerates = {1e-3   : ats.SAMPLE_RATE_1KSPS,
                                  2e-3   : ats.SAMPLE_RATE_2KSPS,
                                  5e-3   : ats.SAMPLE_RATE_5KSPS,
                                  10e-3  : ats.SAMPLE_RATE_10KSPS,
                                  20e-3  : ats.SAMPLE_RATE_20KSPS,
                                  50e-3  : ats.SAMPLE_RATE_50KSPS,
                                  100e-3 : ats.SAMPLE_RATE_100KSPS,
                                  200e-3 : ats.SAMPLE_RATE_200KSPS,
                                  500e-3 : ats.SAMPLE_RATE_500KSPS,
                                  1.     : ats.SAMPLE_RATE_1MSPS,
                                  2.     : ats.SAMPLE_RATE_2MSPS,
                                  5.     : ats.SAMPLE_RATE_5MSPS,
                                  10.    : ats.SAMPLE_RATE_10MSPS,
                                  20.    : ats.SAMPLE_RATE_20MSPS,
                                  50.    : ats.SAMPLE_RATE_50MSPS,
                                  100.   : ats.SAMPLE_RATE_100MSPS,
                                  200.   : ats.SAMPLE_RATE_200MSPS,
                                  500.   : ats.SAMPLE_RATE_500MSPS,
                                  800.   : ats.SAMPLE_RATE_800MSPS,
                                  1e3    : ats.SAMPLE_RATE_1000MSPS,
                                  1.2e3  : ats.SAMPLE_RATE_1200MSPS,
                                  1.5e3  : ats.SAMPLE_RATE_1500MSPS,
                                  1.8e3  : ats.SAMPLE_RATE_1800MSPS}


        self.allow_clock_edges = {'rising'  : ats.CLOCK_EDGE_RISING,
                                  'falling' : ats.CLOCK_EDGE_FALLING}


        self.allow_clock_sources = {'internal' : ats.INTERNAL_CLOCK,
                                    'external' : ats.EXTERNAL_CLOCK_10MHz_REF}

        # By default, we don't take into account the TTL mode for the trigger
        self.allow_trigger_ranges = {5   : ats.ETR_5V,
                                     2.5 : ats.ETR_2V5,
                                     1   : ats.ETR_1V}
                                        #    'TTL' : ats.ETR_TTL}


        self.allow_trigger_slopes = {'positive' : ats.TRIGGER_SLOPE_POSITIVE,
                                    'negative' : ats.TRIGGER_SLOPE_NEGATIVE}



        # Attributes of the clock
        self.samplerate   = 1800. # In [MS/s], float
        self.clock_source = 'external'
        self.clock_edge   = 'rising'

        # Attributes of the trigger
        self.trigger_range = 5. # In [V]
        self.trigger_slope = 'positive'
        self.trigger_level = 0.5 # In [V]
        self.trigger_delay = 0. # In [ns]

        # Attributes of the acquisition
        self.acquired_samples        = 128*80 # In S. Must be integer
        self.acquisition_time        = self.acquired_samples/1.8 # In ns, float
        self.records_per_buffer      = 20 # Must be integer
        self.nb_buffer_allocated     = 40 # Must be integer
        self.nb_buffer_allocated     = 10 # Must be integer
        self.buffers_per_acquisition = 1000 # Must be integer
        self.buffers_per_acquisition = 10 # Must be integer

        # Attributes of data
        self.data_cha = None
        self.data_chb = None

        # Attribut of data treatment
        self.nb_process_data_treatment = 1

        # For the display, we get all parameters at the end of the
        # initialization
        self.get_all()




    def get_all(self):

        self.get_clock_edge()
        self.get_clock_source()
        self.get_samplerate()

        self.get_trigger_level()
        self.get_trigger_range()
        self.get_trigger_slope()
        self.get_trigger_delay()

        self.get_acquisition_time()
        self.get_acquired_samples()
        self.get_buffers_per_acquisition()
        self.get_records_per_buffer()
        self.get_nb_buffer_allocated()

        self.get_nb_process_data_treatment()




#########################################################################
#
#
#                           Methods about the parameters of the board
#
#
#########################################################################



    def _get_bytes_per_buffer(self):
        """
            Return the number ob bytes per buffer of the board.
            The calculation is performed assuming that the board works in the
            NPT mode => no pre-trigger sample.
        """

        # For sake of clarity, even fixed variable are declared
        # The name of the variable is meaningfull
        bitsPerSample      = 12
        preTriggerSamples  = 0 # We assume NPT mode
        postTriggerSamples = self.acquired_samples
        channelCount       = 2 # We assume always two channels active
        recordsPerBuffer   = self.records_per_buffer

        bytesPerSample   = (bitsPerSample + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord   = bytesPerSample * samplesPerRecord
        bytesPerBuffer   = bytesPerRecord * recordsPerBuffer * channelCount

        return int(bytesPerBuffer)




    def _get_parameters(self):
        """
            Create a Manager for the multiprocessing containing all parameters
            needed to tune the board.
            The method returns the manager as pickable variable.
        """

        manager    = mp.Manager()
        parameters = manager.dict()

        # Clock parameters
        parameters['samplerate']   = self.samplerate
        parameters['clock_source'] = self.clock_source
        parameters['clock_edge']   = self.clock_edge

        # Trigger parameters
        parameters['trigger_range'] = self.trigger_range
        parameters['trigger_slope'] = self.trigger_slope
        parameters['trigger_level'] = self.trigger_level
        parameters['trigger_delay'] = self.trigger_delay

        # Acquisition parameters
        parameters['acquired_samples']        = self.acquired_samples
        parameters['records_per_buffer']      = self.records_per_buffer
        parameters['nb_buffer_allocated']     = self.nb_buffer_allocated
        parameters['buffers_per_acquisition'] = self.buffers_per_acquisition

        # correspondence between user parameters and board command
        parameters['allow_samplerates']    = self.allow_samplerates
        parameters['allow_clock_edges']    = self.allow_clock_edges
        parameters['allow_clock_sources']  = self.allow_clock_sources
        parameters['allow_trigger_ranges'] = self.\
                                                   allow_trigger_ranges
        parameters['allow_trigger_slopes'] = self.allow_trigger_slopes

        # Data treatment parameters
        parameters['nb_process_data_treatment'] = self.nb_process_data_treatment

        return parameters





#########################################################################
#
#
#                           Method to perform asynchroneous measurement
#
#
#########################################################################



    def measure(self):

        # We create the Queue to be able to share data between processes
        # Will contain measured data
        queue_data = mp.Queue()
        # manager    = mp.Manager()

        # treat_data = mp.RawArray('d', [0]*self.acquired_samples)
        # finish     = manager.list()

        # for i in range(self.nb_process_data_treatment):
        #     finish.append(False)

        # We get the manager containing all experiment parameters
        parameters = self._get_parameters()


        # We create the Process
        # At this point the process is not start
        worker_acquire_data = mp.Process(target = sub_process.get_data,
                                      args   = (queue_data,
                                                parameters))

        # At this point the process is started
        # Consequently, the measurement is launched.
        worker_acquire_data.start()

        # for i in range(self.nb_process_data_treatment):
        #     worker = mp.Process(target = data_treatment.hum,
        #                                      args   = (queue_data,
        #                                                treat_data,
        #                                                parameters,
        #                                                finish,
        #                                                i))
        #     worker.start()





        # While data_treatment is True, we are treating data
        # Surely, the data acquisition will finish before the data treatment
        # but the worker will be stopped only when the data treatment will be
        # finished.
        # while not all(finish):
        #
        #     pass
        #
        # return np.frombuffer(treat_data), queue_data.get()


        # While data_treatment is True, we are treating data
        # Surely, the data acquisition will finish before the data treatment
        # but the worker will be stopped only when the data treatment will be
        # finished.
        data_treatment = True
        counter = 0.
        while data_treatment:

            # We get data
            data = queue_data.get()

            # We transform data in volt.
            data_volt                    = self.data_in_volt(data)

            # We obtain the current averaging of channel A and B data
            data_cha, data_chb           = self.data_cha_chb(data_volt)

            # We "save" the total averaging in the data attributes.
            self.data_cha, self.data_chb = self.data_average_cha_chb(data_cha,
                                                                     data_chb,
                                                                     counter)

            counter += 1

            # To finish the loop
            if counter == self.buffers_per_acquisition:
                data_treatment = False

        return self.data_cha, self.data_chb, data
        # return data#[::2][10240]


    def measure_2(self):



        board = ats.Board(systemId = 1, boardId = 1)
        samplesPerSec = 1800.e6
        # board.setCaptureClock(ats.INTERNAL_CLOCK,
        #                       ats.SAMPLE_RATE_1800MSPS,
        #                       ats.CLOCK_EDGE_RISING,
        #                       0)

        board.setCaptureClock(ats.EXTERNAL_CLOCK_10MHz_REF,
                              samplesPerSec,
                              ats.CLOCK_EDGE_RISING,
                              1)

        # TODO: Select channel A input parameters as required.
        board.inputControl(ats.CHANNEL_A,
                           ats.DC_COUPLING,
                           ats.INPUT_RANGE_PM_400_MV,
                           ats.IMPEDANCE_50_OHM)


        # TODO: Select channel B input parameters as required.
        board.inputControl(ats.CHANNEL_B,
                           ats.DC_COUPLING,
                           ats.INPUT_RANGE_PM_400_MV,
                           ats.IMPEDANCE_50_OHM)

        # TODO: Select trigger inputs and levels as required.
        board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                  ats.TRIG_ENGINE_J,
                                  ats.TRIG_EXTERNAL,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  150,
                                  ats.TRIG_ENGINE_K,
                                  ats.TRIG_DISABLE,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  128)

        # TODO: Select external trigger parameters as required.
        board.setExternalTrigger(ats.DC_COUPLING,
                                 ats.ETR_5V)
                                #  ats.ETR_TTL)

        # TODO: Set trigger delay as required.
        triggerDelay_sec = 0
        triggerDelay_samples = int(triggerDelay_sec * samplesPerSec + 0.5)
        board.setTriggerDelay(triggerDelay_samples)

        # TODO: Set trigger timeout as required.
        #
        # NOTE: The board will wait for a for this amount of time for a
        # trigger event.  If a trigger event does not arrive, then the
        # board will automatically trigger. Set the trigger timeout value
        # to 0 to force the board to wait forever for a trigger event.
        #
        # IMPORTANT: The trigger timeout value should be set to zero after
        # appropriate trigger parameters have been determined, otherwise
        # the board may trigger if the timeout interval expires before a
        # hardware trigger event arrives.
        triggerTimeout_sec = 0
        triggerTimeout_clocks = int(triggerTimeout_sec / 10e-6 + 0.5)
        board.setTriggerTimeOut(triggerTimeout_clocks)

        # Configure AUX I/O connector as required
        board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                             0)
        # No pre-trigger samples in NPT mode
        preTriggerSamples = 0

        # TODO: Select the number of sam<ples per record.
        postTriggerSamples = 10240
        postTriggerSamples = 128*80

        # TODO: Select the number of records per DMA buffer.
        recordsPerBuffer = 20



        # TODO: Select the active channels.
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0
        for c in ats.channels:
            channelCount += (c & channels == c)

        # TODO: Should data be saved to file?
        saveData = False
        dataFile = None
        if saveData:
            dataFile = open(os.path.join(os.path.dirname(__file__), "data.bin"), 'w')

        # Compute the number of bytes per record and per buffer
        memorySize_samples, bitsPerSample = board.getChannelInfo()
        # print memorySize_samples.value, bitsPerSample.value
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

        # print channelCount

        # TODO: Select number of DMA buffers to allocate
        bufferCount = 10
        # TODO: Select the number of buffers per acquisition.
        # buffersPerAcquisition = bufferCount
        buffersPerAcquisition = 10
        # Allocate DMA buffers
        buffers = []
        for i in range(bufferCount):
            buffers.append(ats.DMABuffer(bytesPerSample, bytesPerBuffer))

        # Set the record size
        board.setRecordSize(preTriggerSamples, postTriggerSamples)

        recordsPerAcquisition = recordsPerBuffer * buffersPerAcquisition

        # Configure the board to make an NPT AutoDMA acquisition
        board.beforeAsyncRead(channels,
                              -preTriggerSamples,
                              samplesPerRecord,
                              recordsPerBuffer,
                              recordsPerAcquisition,
                              ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT | ats.ADMA_FIFO_ONLY_STREAMING)



        # Post DMA buffers to board
        for buffer in buffers:
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        start = time.clock() # Keep track of when acquisition started
        board.startCapture() # Start the acquisition
        print("Capturing %d buffers. Press any key to abort" % buffersPerAcquisition)
        buffersCompleted = 0
        bytesTransferred = 0
        while buffersCompleted < buffersPerAcquisition:
        # for buffer in buffers:
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]

            board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            buffersCompleted += 1
            bytesTransferred += buffer.size_bytes

            # queue_data.put(buffer.buffer)

            # TODO: Process sample data in this buffer. Data is available
            # as a NumPy array at buffer.buffer

            # NOTE:
            #
            # While you are processing this buffer, the board is already
            # filling the next available buffer(s).
            #
            # You MUST finish processing this buffer and post it back to the
            # board before the board fills all of its available DMA buffers
            # and on-board memory.
            #
            # Samples are arranged in the buffer as follows: S0A, S0B, ..., S1A, S1B, ...
            # with SXY the sample number X of channel Y.
            #
            # A 12-bit sample code is stored in the most significant bits of
            # in each 16-bit sample value.
            #
            # Sample codes are unsigned by default. As a result:
            # - a sample code of 0x0000 represents a negative full scale input signal.
            # - a sample code of 0x8000 represents a ~0V signal.
            # - a sample code of 0xFFFF represents a positive full scale input signal.
            # Optionaly save data to file
            if dataFile:
                buffer.buffer.tofile(dataFile)

            # Update progress bar
            #waitBar.setProgress(buffersCompleted / buffersPerAcquisition)

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
        # Compute the total transfer time, and display performance information.
        transferTime_sec = time.clock() - start
        print("Capture completed in %f sec" % transferTime_sec)
        buffersPerSec = 0
        bytesPerSec = 0
        recordsPerSec = 0
        samplesTransferred = samplesPerRecord*recordsPerBuffer*buffersPerAcquisition
        if transferTime_sec > 0:
            buffersPerSec = buffersCompleted / transferTime_sec
            bytesPerSec = bytesTransferred / transferTime_sec
            recordsPerSec = recordsPerBuffer * buffersCompleted / transferTime_sec
            samplePerSec  = samplesTransferred / transferTime_sec
        print("Captured %d buffers (%f buffers per sec)" % (buffersCompleted, buffersPerSec))
        print("Captured %d records (%f records per sec)" % (recordsPerBuffer * buffersCompleted, recordsPerSec))
        print("Transferred %d bytes (%f Gbytes per sec)" % (bytesTransferred, bytesPerSec/1024**3.))
        print("Transferred %d samples (%f GS per sec)" % (samplesTransferred, samplePerSec/1e9))

        # Abort transfer.
        board.abortAsyncRead()
        return buffers


#########################################################################
#
#
#                           Method to treat data
#
#
#########################################################################


    def data_average_cha_chb(self, data_cha, data_chb, current_iteration):
        """
            Perform the averaging of acquired data following the number of
            iteration at which the averaging is done.
            The return averaging is then always the arithmetic averaging of
            the measured data.

            current_iteration must start from 0.
        """
        # For the first iteration, the averaging is just an addition
        if current_iteration == 0.:
            data_cha += data_cha
            data_chb += data_chb
        # For all other iterations, we perform the averaging
        else:
            data_cha = data_cha*current_iteration/(current_iteration + 1.)\
                       + data_cha/(current_iteration + 1.)
            data_chb = data_chb*current_iteration/(current_iteration + 1.)\
                       + data_chb/(current_iteration + 1.)

        return data_cha, data_chb


    def data_cha_chb(self, data_volt):
        """
            From the data returned by the board and transormed in data_volt,
            the method splits data coming from the two channels and make the
            averaging on one buffer.
        """

        # We split the two channels
        data_cha = data_volt[ ::2]
        data_chb = data_volt[1::2]

        # We reshape them in 2D-array to enhance the averaging
        data_cha = np.reshape(data_cha, (self.records_per_buffer,
                                         self.acquired_samples))
        data_chb = np.reshape(data_chb, (self.records_per_buffer,
                                         self.acquired_samples))

        # We average along the axis of the repetitions
        data_cha = np.mean(data_cha, axis = 0)
        data_chb = np.mean(data_chb, axis = 0)

        return data_cha, data_chb



    def data_in_volt(self, data):
        """
            Get raw data coming from the board and transform them in V.
        """

        # Parameters of the board (are fixed).
        bitshift         = 4  # Sould be int
        bits_per_sample  = 12 # Sould be int
        inputRange_volts = 400e-3

        # Right-shift 16-bit sample value by 4 to get 12-bit sample code
        sampleCode = data >> bitshift

        # AlazarTech digitizers are calibrated as follows
        codeZero  = (1 << (bits_per_sample - 1)) - 0.5
        codeRange = (1 << (bits_per_sample - 1)) - 0.5

        # Simple proportionality
        sampleVolts = inputRange_volts*(sampleCode - codeZero) / codeRange

        return sampleVolts




#########################################################################
#
#
#                           Data treatment
#
#
#########################################################################

    def do_set_nb_process_data_treatment(self, nb_process_data_treatment):
        '''Set the number of process dedicated to data treatment

            Input:
                - nb_process_data_treatment (int) :number of process dedicated
                  to data treatment


            Output:
                - None
            '''

        if nb_process_data_treatment < 1:

            raise ValueError('The number of process dedicated to data\
                              treatment must be greater than 1')
        else:

            self.nb_process_data_treatment = nb_process_data_treatment




    def do_get_nb_process_data_treatment(self):
        '''Get the number of process dedicated to data treatment

            Input:
                - None.

            Output:
                - nb_process_data_treatmen
        '''

        return self.nb_process_data_treatment






#########################################################################
#
#
#                           Acquisition
#
#
#########################################################################

    def do_set_acquisition_time(self, acquisition_time):
        '''Set the acquisition time in [ns]

            Input:
                - acquisition_time (float): The acquisition time in [ns].
                 The minimum number of sample being 256.
                 The minimum acquisition time is then 256/samplerate.
                 The acquisition time will be round the closest value reachable
                 considering the samplerate.

                 The number of acquired sample must a multiple of 128.
                 The number of acquired sample will be round the closest value
                 reachable.


            Output:
                - None

                # - acquisition_time (float): The acquisition time in [ns] set
                #  in the board.
                #  - acquisition_samples (int): The number of acquired sample set
                #   in the board.
            '''

        if acquisition_time > 256./self.samplerate*1e3:

            acquired_samples = round(self.samplerate*acquisition_time*1e-3)
            self.acquired_samples = int(round(acquired_samples/128)*128)
            acquisition_time_code = self.acquired_samples/self.samplerate/1e6
            self.acquisition_time = acquisition_time_code*1e9

            # To display the new value of acquired sample of get it
            self.get_acquired_samples()

            # return self.acquisition_time, self.acquired_samples
        else:

            raise ValueError('The acquisition time must be longer than '\
                             +str(round(256./self.samplerate*1e3,2))+' ns.')




    def do_get_acquisition_time(self):
        '''Get the acquisition time in [ns]

            Input:
                - None.

            Output:
                - acquisition_time (float): The acquisition time in [ns].
        '''

        return self.acquisition_time





    def do_get_acquired_samples(self):
        '''Get the number of acquired samples in [S]

            Input:
                - None.

            Output:
                - acquired_samples (int): The number of acquired samples in [S]
        '''

        return self.acquired_samples




    def do_set_buffers_per_acquisition(self, buffers_per_acquisition):
        '''
            Set the number of buffer during an acquisition

            Input:
                - buffers_per_acquisition (int): number of buffer during an
                 acquisition.

            Output:
                - None.
        '''

        self.buffers_per_acquisition = int(buffers_per_acquisition)


    def do_get_buffers_per_acquisition(self):
        '''
            Get the number of buffer during an acquisition

            Input:
                - None.

            Output:
                - buffers_per_acquisition (int): number of buffer during an
                 acquisition.
        '''

        return self.buffers_per_acquisition




    def do_set_records_per_buffer(self, records_per_buffer):
        '''
            Set the number of records per buffer

            Input:
                - records_per_buffer (int): number of records per buffer

            Output:
                - None.
        '''

        self.records_per_buffer = int(records_per_buffer)


    def do_get_records_per_buffer(self):
        '''
            Get the number of buffer during an acquisition

            Input:
                - None.

            Output:
                - records_per_buffer (int): number of records per buffer
        '''

        return self.records_per_buffer


    def do_set_nb_buffer_allocated(self, nb_buffer_allocated):
        '''
            Set the number of buffer allocated for an acquisition

            Input:
                - nb_buffer_allocated (int): number of buffer allocated for an
                 acquisition

            Output:
                - None.
        '''

        self.nb_buffer_allocated = int(nb_buffer_allocated)


    def do_get_nb_buffer_allocated(self):
        '''
            Get the number of buffer allocated for an acquisition

            Input:
                - None.

            Output:
                - nb_buffer_allocated (int): number of buffer allocated for an
                 acquisition
        '''

        return self.nb_buffer_allocated



#########################################################################
#
#
#                           The trigger
#
#
#########################################################################


    def do_set_trigger_delay(self, trigger_delay):
        '''
            Set the waitting time after which the board has received a trigger
            event before capturing a record in [ns]

            Input:
                - trigger_delay (float): Triger delay in [ns]

            Output:
                - None.
        '''

        self.trigger_delay = trigger_delay


    def do_get_trigger_delay(self):
        '''
            Get the trigger delay in [ns]

            Input:
                - None.

            Output:
                - trigger_delay (float): Triger delay in [ns]
        '''

        return self.trigger_delay






    def do_set_trigger_level(self, trigger_level):
        '''
            Set the level that the trigger source must rise above, or fall
            below, for the selected trigger to become active.

            Input:
                - trigger_level (float): Triger level in [V]
                Must be in the limit of the trigger range.

            Output:
                - None.
        '''

        # If the trigger level is in the trigger range, we accept it
        if trigger_level <  self.trigger_range and \
            trigger_level > -self.trigger_range :

            self.trigger_level = trigger_level
        else:
            raise ValueError('The trigger level must be in the input range\
                             of the trigger, here '+str(self.trigger_range)\
                             +' V.')


    def do_get_trigger_level(self):
        '''
            Get the trigger level in [V]

            Input:
                - None.

            Output:
                - trigger_level (float): Triger level in [V]
        '''

        return self.trigger_level






    def do_set_trigger_range(self, trigger_range):
        '''Set the input range of the trigger channel in [V].

            Input:
                - trigger_range (float|int): Select input range of the
                 trigger channel. Must be [5, 2.5, 1] [V].
                 The new trigger range has to contain the trigger level

            Output:
                - None.
        '''

        if trigger_range > self.trigger_level :

            self.trigger_range = trigger_range
        else:

            raise ValueError('The trigger range must contain the trigger level')


    def do_get_trigger_range(self):
        '''Get the input range of the trigger channel.

            Input:
                - None.

            Output:
                - trigger_range (float|int): Input range of the
                 trigger channel [5, 2.5, 1].
        '''

        return self.trigger_range




    def do_set_trigger_slope(self, trigger_slope):
        '''
            Set the sign of the rate of change of the trigger signal
            with time when it crosses the trigger voltage level that is
            required to generate a trigger event.

            Input:
                - trigger_range (string): ['positive', 'negative'].

            Output:
                - None.
        '''
        self.trigger_slope = trigger_slope.lower()


    def do_get_trigger_slope(self):
        '''
            Get the sign of the rate of change of the trigger signal
            with time when it crosses the trigger voltage level that is
            required to generate a trigger event.

            Input:
                - None.

            Output:
                - trigger_range (string): ['positive', 'negative'].
        '''

        return self.trigger_slope









#########################################################################
#
#
#                           The clock
#
#
#########################################################################


    def do_set_clock_edge(self, clock_edge):
        '''Set the clock edge of the board.

            Input:
                - clock_edge (string): Select the external clock edge on which
                                       to latch samples data. Must be either
                                       "rising" or "failing".

            Output:
                - None.
        '''

        if clock_edge.lower() in self.allow_clock_edges:

            self.clock_edge = clock_edge.lower()
        else:
            raise ValueError('Samplerate not allowed by the board')



    def do_get_clock_edge(self):
        '''Get the clock edge of the board.

            Input:
                - None.

            Output:
                - clock_edge (string): The external clock edge on which
                                       to latch samples data. Either
                                       "rising" or "failing".
        '''

        return self.clock_edge


    def do_set_samplerate(self, samplerate):
        '''Set the samplerate of the board.

            Input:
                - samplerate (float): If the clock source is internal
                  the samplerate must be one of the following string: 1e-3,
                  2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1.,
                  2., 5., 10., 20., 50., 100., 200., 500., 800., 1e3, 1.2e3,
                  1.5e3, 1.8e3.

                  If the clock is set to be external (assumed 10MHz external
                  clock), all samplerates greater than 300MHz and smaller than
                  1800MHZ being a multiple of 1 MHz are allowed [should be
                  given in MS/s].

            Output:
                - None.
        '''

        # If the board uses its internal clock, only certains samplerate are
        # allowed, see dictionnary self.samplerates.

        # If the board uses its external clock, all samplerates greater than
        # 300MHz and smaller than 1800MHZ being a multiple of 1 MHz are
        # allowed.

        if self.clock_source == 'internal':

            if samplerate in self.allow_samplerates:

                self.samplerate = float(samplerate)
            else:

                raise ValueError('Samplerate not allowed by the board')

        elif self.clock_source == 'external':

            if samplerate > 300. and samplerate < 1800.:

                self.samplerate = float(samplerate)
            else:

                raise ValueError('Samplerate not allowed by the board')
        else:

            raise ValueError('The clock source must be set to "internal"\
                              or "external".')


    def do_get_samplerate(self):
        '''Get the samplerate of the board.

            Input:
                -

            Output:
                -
        '''

        return self.samplerate



    def do_set_clock_source(self, clock_source):
        '''Set the clock source of the board.

            Input:
                - clock_source (string): Must be either "internal" or
                 "external".

            Output:
                - None.
        '''

        if clock_source.lower() in self.allow_clock_sources:

            self.clock_source = clock_source.lower()
        else:

            raise ValueError('clock_source argument must be "internal" or \
                             "external"')





    def do_get_clock_source(self):
        '''Get the clock source of the board.

            Input:
                -

            Output:
                -
        '''

        return self.clock_source