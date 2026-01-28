from machine import Pin, SoftI2C                                              
from time import sleep_ms                                                     
                                                                            
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=50000)                             
sleep_ms(1000)                                                                
print([hex(d) for d in i2c.scan()])                                           
                                       
