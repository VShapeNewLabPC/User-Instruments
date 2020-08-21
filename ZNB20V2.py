# ZNB20.py is a driver for Rohde & Schwarz ZNB20 Vector Network Analyser
# written by Thomas Weissl, modified by Nico Roch and Yuriy Krupko, 2014
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
import qt
import visa
import logging
import types
from numpy import pi
import numpy as np

class ZNB20V2(Instrument):
    '''
    This is the python driver for the ZNB20

    Usage:
    Initialize with
    <name> = instruments.create('name', 'ZNB20', address='<GPIB address>', reset=True|False)
    '''

    def __init__(self, name, address, reset = False):
        '''
        Initializes the ZNB20

        Input:
            name (string)    : name of the instrument
            address (string) : TCPIP/GPIB address
            reset (bool)     : Reset to default values

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')

        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()

        self._address = address

        try:
            self._visainstrument = rm.open_resource(self._address)
        except:
            raise SystemExit
        self._visainstrument.write_termination = '\n'
        self._visainstrument.read_termination = '\n'

        self.add_parameter('frequencyspan', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('centerfrequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('startfrequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('stopfrequency', flags=Instrument.FLAG_GETSET, units='Hz', minval=100e3, maxval=20e9, type=types.FloatType)
        self.add_parameter('power', flags=Instrument.FLAG_GETSET, units='dBm', maxval=30.0, type=types.FloatType)
        self.add_parameter('averages', flags=Instrument.FLAG_GETSET, units='', maxval=100000, type=types.FloatType)
        self.add_parameter('averagestatus', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('points', flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=100000, type=types.IntType)
        self.add_parameter('sweeps', flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=1000, type=types.FloatType)
        self.add_parameter('measBW', flags=Instrument.FLAG_GETSET, units='Hz', minval=0.1, maxval=500e3, type=types.FloatType)
        self.add_parameter('status', flags=Instrument.FLAG_GETSET, option_list=['on', 'off'], type=types.StringType)
        self.add_parameter('cwfrequency', flags=Instrument.FLAG_GETSET, units='GHz', minval=1e-4, maxval=20, type=types.FloatType)

        self.add_function('get_all')
        self.add_function('reset')
        self.add_function('create_trace')

        if reset :

            self.reset()

        #self.get_all()

###################################################################
#
#                Methods
#
###################################################################

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')


    def get_all(self):
        '''
        Get all parameters of the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_frequencyspan()
        self.get_centerfrequency()
        self.get_startfrequency()
        self.get_stopfrequency()
        self.get_power()
        self.get_averages()
        self.get_averagestatus()
        self.get_points()
        self.get_sweeps()
        self.get_measBW()
        self.get_status()
        self.get_cwfrequency()
        self.get_freqpoints()

    def create_trace(self,trace,Sparam):
        '''
        creates a trace to measure Sparam and displays it

        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ + ' : create trace')
        self._visainstrument.write('calc:parameter:del:all ')
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace,Sparam))
        #self._visainstrument.write('calc:parameter:del  "Trc1"')
        #self._visainstrument.write('disp:wind1:stat off')
        self._visainstrument.write('disp:wind1:stat on')
        self._visainstrument.write('disp:wind1:trac1:feed "%s"' % trace)
        self._visainstrument.write('syst:disp:upd on')
        self._visainstrument.write('init:cont off')

    def create_2trace(self,trace1,Sparam1,trace2,Sparam2):
        '''
        creates a trace to measure Sparam and displays it

        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ + ' : create trace')
        self._visainstrument.write('calc:parameter:del:all ')
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace1,Sparam1))
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace2,Sparam2))
        #self._visainstrument.write('disp:wind1:stat off')
        self._visainstrument.write('disp:wind1:stat on')
        self._visainstrument.write('disp:wind1:trac1:feed "%s"' % trace1)
        self._visainstrument.write('disp:wind1:trac2:feed "%s"' % trace2)
        self._visainstrument.write('syst:disp:upd on')
        self._visainstrument.write('init:cont off')


    def create_4trace(self,trace1,Sparam1,trace2,Sparam2,trace3,Sparam3,trace4,Sparam4):
        '''
        creates a trace to measure Sparam and displays it

        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ + ' : create trace')
        self._visainstrument.write('calc:parameter:del:all ')
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace1,Sparam1))
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace2,Sparam2))
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace3,Sparam3))
        self._visainstrument.write('calc:parameter:sdef  "%s","%s"' %(trace4,Sparam4))
        #self._visainstrument.write('disp:wind1:stat off')
        self._visainstrument.write('disp:wind1:stat on')
        self._visainstrument.write('disp:wind1:trac1:feed "%s"' % trace1)
        self._visainstrument.write('disp:wind1:trac2:feed "%s"' % trace2)
        self._visainstrument.write('disp:wind1:trac3:feed "%s"' % trace3)
        self._visainstrument.write('disp:wind1:trac4:feed "%s"' % trace4)
        self._visainstrument.write('syst:disp:upd on')
        self._visainstrument.write('init:cont off')



    def measure(self):
        '''
        creates a trace to measure Sparam and displays it

        Input:
            trace (string, Sparam ('S11','S21','S12','S22')

        Output:
            None

        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')
        self._visainstrument.write('initiate:cont off')
        #Set the standard event register (ESR) to zero
        self._visainstrument.write('*CLS')
        #self._visainstrument.write('init:imm')
		#self._visainstrument.write('*WAI')
        #self._visainstrument.write('*OPC')
        self._visainstrument.write('INITiate1:IMMediate; *OPC')

    def gettrace(self):
        '''
        reads a trace from znb

        Input:

            trace (string)

        Output:

            None
        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')


        while self._visainstrument.query('*ESR?') != '1':
            qt.msleep(0.1)
        else:
            #dstring=self._visainstrument.query('calculate:Data:NSweep? Sdata, 1 ')
            dstring=self._visainstrument.query('calculate:Data? Sdata')
            #self._visainstrument.write('init:cont on')
            dstringclean=dstring.split(';')[0]
            real,im= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T
            return real+im*1j

    def get2trace(self,trace1,trace2):
        '''
        reades 2 traces from znb

        Input:

            trace (string)

        Output:

            None
        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')


        while self._visainstrument.query('*ESR?') != '1':
            qt.msleep(0.1)
        else:
			self._visainstrument.write('calc:parameter:sel  "%s"' %(trace1))
			dstring=self._visainstrument.query('calculate:Data? Sdata')
			dstringclean=dstring.split(';')[0]
			real1,im1= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T

			self._visainstrument.write('calc:parameter:sel  "%s"' %(trace2))
			dstring=self._visainstrument.query('calculate:Data? Sdata')
			dstringclean=dstring.split(';')[0]
			real2,im2= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T

			return real1+im1*1j,real2+im2*1j


    def get4trace(self,trace1,trace2,trace3,trace4):
        '''
        reades 4 traces from znb

        Input:

            trace (string)

        Output:

            None
        '''
        logging.info(__name__ + ' : start to measure and wait till it is finished')


        while self._visainstrument.query('*ESR?') != '1':
            qt.msleep(0.1)
        else:
			self._visainstrument.write('calc:parameter:sel  "%s"' %(trace1))
			dstring=self._visainstrument.query('calculate:Data? Sdata')
			dstringclean=dstring.split(';')[0]
			real1,im1= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T

			self._visainstrument.write('calc:parameter:sel  "%s"' %(trace2))
			dstring=self._visainstrument.query('calculate:Data? Sdata')
			dstringclean=dstring.split(';')[0]
			real2,im2= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T

			self._visainstrument.write('calc:parameter:sel  "%s"' %(trace3))
			dstring=self._visainstrument.query('calculate:Data? Sdata')
			dstringclean=dstring.split(';')[0]
			real3,im3= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T

			self._visainstrument.write('calc:parameter:sel  "%s"' %(trace4))
			dstring=self._visainstrument.query('calculate:Data? Sdata')
			dstringclean=dstring.split(';')[0]
			real4,im4= np.reshape(np.array(dstringclean.split(','),dtype=float),(-1,2)).T

			#estring=self._visainstrument.query('system:error:all?')
			#print estring

			return real1+im1*1j,real2+im2*1j,real3+im3*1j,real4+im4*1j


    def averageclear(self):
        '''
        Starts a new average cycle


        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : clear average')
        self._visainstrument.write('AVERage:CLEar')

    def set_trigger(self, trigger='IMM'):
        '''
    	Define the source of the trigger: IMMediate (free run measurement or untriggered), EXTernal, MANual or MULTiple

        Input:
            trigger (string): IMM, EXT, MAN or MULT
        Output:
            None
        '''
        logging.debug(__name__ + ' : The source of the trigger is set to %s' % trigger)
        if trigger.upper() in ('IMM'):
            self._visainstrument.write('TRIG:SOUR IMM')
        elif trigger.upper() in ('EXT'):
            self._visainstrument.write('TRIG:SOUR EXT')
        elif trigger.upper() in ('MAN'):
            self._visainstrument.write('TRIG:SOUR MAN')
        elif trigger.upper() in ('MULT'):
            self._visainstrument.write('TRIG:SOUR MULT')
        else:
            raise ValueError('set_trigger(): can only set IMM, EXT, MAN or MULT')

    def set_trigger_link(self, link='POIN'):
        '''
        Define the link of the trigger: SWEep (trigger event starts an entire sweep), SEGMent (trigger event starts a sweep segment), POINt (trigger event starts measurement at the next sweep point) or PPOint (trigger event starts the next partial measurement at the current or at the next sweep point).

        Input:
            lin (string): SWE, SEGM, POIN or PPO
        Output:
            None
        '''
        logging.debug(__name__ + ' : The link of the trigger is set to %s' % link)

        if link.upper() in ('SWE', 'SEGM', 'POIN', 'PPO'):
            self._visainstrument.write("TRIG:LINK '"+str(link.upper())+"'")
        else:
            raise ValueError('set_trigger(): can only set  SWE, SEGM, POIN or PPO')
	
    def set_sweeptype(self, sweeptype='LIN'):
        '''
    	Define the type of the sweep: LINear | LOGarithmic | POWer | CW | POINt | SEGMent

        Input:
            sweeptype (string): LIN, LOG, POW, CW, POIN or SEG
        Output:
            None
        '''
        logging.debug(__name__ + ' : The type of the sweep is set to %s' % sweeptype)
        if sweeptype.upper() in ('LIN'):
            self._visainstrument.write('SWE:TYPE LIN')
        elif sweeptype.upper() in ('LOG'):
            self._visainstrument.write('SWE:TYPE LOG')
        elif sweeptype.upper() in ('POW'):
            self._visainstrument.write('SWE:TYPE POW')
        elif sweeptype.upper() in ('CW'):
            self._visainstrument.write('SWE:TYPE CW')
        elif sweeptype.upper() in ('POIN'):
            self._visainstrument.write('SWE:TYPE POIN')
        elif sweeptype.upper() in ('SEG'):
            self._visainstrument.write('SWE:TYPE SEG')
        else:
            raise ValueError('set_sweeptype(): can only set LIN, LOG, POW, CW, POIN or SEG')

    def get_freqpoints(self):
        '''
            Gets the frequency points of the sweep using 
            get_startfrequency and get_stopfrequency.
            
            Input:
                None
                
            Output:
                frequency_points (numpy.array): array with the frequency values of the sweep.
        '''
        frequency_points = np.linspace(self.get_startfrequency(),self.get_stopfrequency(),self.get_points())
        return frequency_points
        
    def get_sweeptime(self):
        '''
            Gets the time duration of a sweep.
            
            Input:
                None
                
            Output:
                sweep_time (float): sweep duration in seconds.
        '''
        
        sweep_time = self.get_points()/self.get_measBW()
        return sweep_time
        
    def get_sweeptime_averages(self):
        '''
            Gets the time duration of a sweep taking into account the average
            
            Input:
                None
                
            Output:
                sweep_time_averages (float): sweep duration times average in seconds
        '''
        
        sweep_time_averages = self.get_sweeptime()*self.get_averages()
        return sweep_time_averages
#########################################################
#
#                  Write and Read from VISA
#
#########################################################

    def tell(self, cmd):
        self._visainstrument.write(cmd)
    def query(self, cmd):
        res= self._visainstrument.query(cmd + '?')
        print res
        return res

#########################################################
#
#                Frequency
#
#########################################################

    def do_set_centerfrequency(self, centerfrequency=1.):
        '''
            Set the center frequency of the instrument

            Input:
                frequency (float): Center frequency at which the instrument will measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:center '+str(centerfrequency))


    def do_get_centerfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:center?')

    def do_set_frequencyspan(self, frequencyspan=1.):
        '''
            Set the frequency span of the instrument

            Input:
                frequency (float): Frequency span at which the instrument will measure [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('FREQ:SPAN '+str(frequencyspan))


    def do_get_frequencyspan(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:span?')


    def do_set_startfrequency(self, startfrequency=1.):
        '''
            Set the start frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:start '+str(startfrequency))


    def do_get_startfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:start?')

    def do_set_stopfrequency(self, stopfrequency=1.):
        '''
            Set the start frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the frequency of the instrument')
        self._visainstrument.write('frequency:stop '+str(stopfrequency))


    def do_get_stopfrequency(self):
        '''
            Get the frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the frequency of the instrument')
        return self._visainstrument.query('frequency:stop?')

    def do_set_cwfrequency(self, cwfrequency=1.):
        '''
            Set the CW frequency of the instrument

            Input:
                frequency (float): Frequency at which the instrument will be tuned [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the CW frequency of the instrument')
        self._visainstrument.write('SOUR:FREQ:CW '+str(cwfrequency)+ 'GHz')

    def do_get_cwfrequency(self):
        '''
            Get the CW frequency of the instrument

            Input:
                None

            Output:
                frequency (float): frequency at which the instrument has been tuned [Hz]
        '''

        logging.info(__name__+' : Get the CW frequency of the instrument')
        return self._visainstrument.query('SOUR:FREQ:CW?')


        
#########################################################
#
#                Power
#
#########################################################

    def do_set_power(self, power=0):
        '''
            Set the power of the instrument


            Input:
                power (float): power at which the instrument will be tuned [dBm]

            Output:
                None
        '''

        logging.info(__name__+' : Set the power of the instrument')
        self._visainstrument.write('source:power '+str(power))


    def do_get_power(self):
        '''
            Get the power of the instrument

            Input:
                None

            Output:

                power (float): power at which the instrument has been tuned [dBm]
        '''

        logging.info(__name__+' : Get the power of the instrument')
        return self._visainstrument.query('source:power?')

#########################################################
#
#                Averages
#
#########################################################

    def do_set_averages(self, averages=1):
        '''
            Set the averages of the instrument


            Input:
                phase (float): averages at which the instrument will be tuned [rad]

            Output:
                None
        '''

        logging.info(__name__+' : Set the averages of the instrument')
        self._visainstrument.write('average:count '+str(averages))


    def do_get_averages(self):
        '''
            Get the phase of the instrument


            Input:
                None

            Output:

                phase (float): averages of the instrument
        '''

        logging.info(__name__+' : Get the averages of the instrument')
        return self._visainstrument.query('average:count?')

    def do_get_averagestatus(self):
        """
        Reads the output status from the instrument

        Input:
            None


        Output:
            status (string) : 'on' or 'off'
        """
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.query('average?')
        if stat=='1':
          return 'on'
        elif stat=='0':
          return 'off'
        else:
		  raise ValueError('Output status not specified : %s' % stat)

    def do_set_averagestatus(self, status='off'):
        '''
        Set the output status of the instrument


        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('average %s' % status.upper())


#########################################################
#
#                BW
#
#########################################################

    def do_set_measBW(self, measBW=1000):
        '''
            Set the measurement bandwidth of the instrument



            Input:
                measBW (float): measurement bandwidth [Hz]

            Output:
                None
        '''

        logging.info(__name__+' : Set the measurement bandwidth of the instrument')
        self._visainstrument.write('sens:band '+str(measBW))


    def do_get_measBW(self):
        '''
            Get the BW of the instrument

            Input:
                None

            Output:


                BW (float): measurement bandwidth [Hz]
        '''

        logging.info(__name__+' : Get the BW of the instrument')
        return self._visainstrument.query('sens:band?')


#########################################################
#
#                Points
#
#########################################################

    def do_set_points(self, points=1001):
        '''
            Set the points of the instrument


            Input:
                points (integer): number of points of the sweep

            Output:
                None
        '''

        logging.info(__name__+' : Set the power of the instrument')
        self._visainstrument.write('sens:sweep:points '+str(points))


    def do_get_points(self):
        '''
            Get the points of the instrument

            Input:
                None

            Output:

                points (integer): number of points of the sweep
        '''

        logging.info(__name__+' : Get sweep number of points')
        return self._visainstrument.query('sens:sweep:points?')

#########################################################
#
#                Sweeps
#
#########################################################

    def do_set_sweeps(self, sweeps=1):
        '''
            Set the points of the instrument


            Input:
                power (float): sweeps of the instrument will be tuned

            Output:
                None
        '''

        logging.info(__name__+' : Set the power of the instrument')
        self._visainstrument.write('initiate:cont Off ')
        self._visainstrument.write('sens:sweep:count '+str(sweeps))


    def do_get_sweeps(self):
        '''
            Get the points of the instrument

            Input:
                None

            Output:

                BW (float):sweeps at which the instrument
        '''

        logging.info(__name__+' : Get the sweeps of the instrument')
        return self._visainstrument.query('sens:sweep:count?')

#########################################################
#
#                Status
#
#########################################################

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.query('output?')

        if (stat=='1'):
          return 'on'
        elif (stat=='0'):
          return 'off'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status='off'):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('output %s' % status)
