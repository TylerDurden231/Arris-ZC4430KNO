# -*- coding: utf-8 -*-
# Model = Arris ZC4430KNO (UMA2)
# Test name = Autodiag
# Test description = Check autodiag tests

from datetime import datetime
import time
import device
import TEST_CREATION_API
import shutil
import os.path
import sys
import telnetlib

try:    
    if ((os.path.exists(os.path.join(os.path.dirname(sys.executable), "Lib\NOS_API.py")) == False) or (str(os.path.getmtime('\\\\rt-rk01\\RT-Executor\\API\\NOS_API.py')) != str(os.path.getmtime(os.path.join(os.path.dirname(sys.executable), "Lib\NOS_API.py"))))):
        shutil.copy2('\\\\rt-rk01\\RT-Executor\\API\\NOS_API.py', os.path.join(os.path.dirname(sys.executable), "Lib\NOS_API.py"))
except:
    pass

import NOS_API
  
try:
    # Get model
    model_type = NOS_API.get_model()

    # Check if folder with thresholds exists, if not create it
    if(os.path.exists(os.path.join(os.path.dirname(sys.executable), "Thresholds")) == False):
        os.makedirs(os.path.join(os.path.dirname(sys.executable), "Thresholds"))

    # Copy file with threshold if does not exists or if it is updated
    if ((os.path.exists(os.path.join(os.path.dirname(sys.executable), "Thresholds\\" + model_type + ".txt")) == False) or (str(os.path.getmtime(NOS_API.THRESHOLDS_PATH + model_type + ".txt")) != str(os.path.getmtime(os.path.join(os.path.dirname(sys.executable), "Thresholds\\" + model_type + ".txt"))))):
        shutil.copy2(NOS_API.THRESHOLDS_PATH + model_type + ".txt", os.path.join(os.path.dirname(sys.executable), "Thresholds\\" + model_type + ".txt"))
except Exception as error_message:
    pass

## Number of alphanumeric characters in SN
SN_LENGTH = 16 

## Number of alphanumeric characters in Cas_Id
CASID_LENGTH = 12

## Number of alphanumeric characters in MAC
MAC_LENGTH = 12

## Wait to Autodiag app appears
WAIT_AUTODIAG_START = 10

## Wait first test in autodiag appears
WAIT_AUTODIAG_TEST = 60

## Number of attempts to open Autodiag app
ATTEMPT_OPEN_AUTODIAG = 3

## CPU Temperature Threshold
CPU_Temperature_Threshold = 100

## Lenght of Recorded Video in ms
MAX_RECORD_VIDEO_TIME = 4000

## Lenght of Recorded Audio in ms
MAX_RECORD_AUDIO_TIME = 2000

def runTest():
    System_Failure = 0
    while (System_Failure < 2):
        try:    
            NOS_API.grabber_hour_reboot()
            
            NOS_API.read_thresholds()
            
            NOS_API.reset_test_cases_results_info()  
            
            ## Set test result default to FAIL
            test_result = "FAIL"
            
            ## Set Labels Check Variables to False
            SN_LABEL = False
            CASID_LABEL = False
            MAC_LABEL = False  
        
            ## Set all test cases to False
            AutoDiag_Test = False
            Upgrade_Test = False
            STB_Info_Test = False
            WiFi_Test = False
            Front_Panel = False
            Equipment_Test = False
            Peripherals_Test = False
            Bluetooth_Test = False
            HDMI_HD_1080_Test = False
            HDMI_SD_720_Test = False
            HDMI_4k_2160_Test = False
            
            ## Set Error Codes and Error Messages to Empty
            error_codes = ""
            error_messages = ""
            
            ## Initialization of other variables
            software_version = ""
            counter = 0
            timeout = 0
            Upgrade_Tries = 0
            Upgrade_Time = 30
            BluetoothTries = 0
            BluetoothTriesThreshold = 5
            Grabber_Init = 0
            
            ### Initialize grabber device
            #NOS_API.initialize_grabber()
            #
            ### Start grabber device with video on default video source
            #NOS_API.grabber_start_video_source(TEST_CREATION_API.VideoInterface.HDMI1)
            ### Start grabber device with audio on default audio source
            #TEST_CREATION_API.grabber_start_audio_source(TEST_CREATION_API.AudioInterface.HDMI1)
            
            try:      
                all_scanned_barcodes = NOS_API.get_all_scanned_barcodes()
                NOS_API.test_cases_results_info.s_n_using_barcode = all_scanned_barcodes[1]
                NOS_API.test_cases_results_info.cas_id_using_barcode = all_scanned_barcodes[2]
                NOS_API.test_cases_results_info.mac_using_barcode = all_scanned_barcodes[3]
                NOS_API.test_cases_results_info.nos_sap_number = all_scanned_barcodes[0]
            except Exception as error:
                TEST_CREATION_API.write_log_to_file(error)
                test_result = "FAIL"        
                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.scan_error_code \
                                                   + "; Error message: " + NOS_API.test_cases_results_info.scan_error_message)
                NOS_API.set_error_message("Leitura de Etiquetas")
                error_codes = NOS_API.test_cases_results_info.scan_error_code
                error_messages = NOS_API.test_cases_results_info.scan_error_message 
                
                NOS_API.add_test_case_result_to_file_report(
                                test_result,
                                "- - - - - - - - - - - - - - - - - - - -",
                                "- - - - - - - - - - - - - - - - - - - -",
                                error_codes,
                                error_messages)
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                report_file = ""    
                if (test_result != "PASS"):
                    report_file = NOS_API.create_test_case_log_file(
                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                    NOS_API.test_cases_results_info.nos_sap_number,
                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                    end_time)
                    NOS_API.upload_file_report(report_file) 
                    NOS_API.test_cases_results_info.isTestOK = False
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                            test_result,
                            end_time,
                            error_codes,
                            report_file)
            
                ## Update test result
                TEST_CREATION_API.update_test_result(test_result)
            
                ## Return DUT to initial state and de-initialize grabber device
                NOS_API.deinitialize()
                return
             
            test_number = NOS_API.get_test_number(NOS_API.test_cases_results_info.s_n_using_barcode)
            device.updateUITestSlotInfo("Teste N\xb0: " + str(int(test_number)+1))
            
            if ((len(NOS_API.test_cases_results_info.s_n_using_barcode) == SN_LENGTH) and (NOS_API.test_cases_results_info.s_n_using_barcode.isalnum() or NOS_API.test_cases_results_info.s_n_using_barcode.isdigit())):
                SN_LABEL = True

            if ((len(NOS_API.test_cases_results_info.cas_id_using_barcode) == CASID_LENGTH) and (NOS_API.test_cases_results_info.cas_id_using_barcode.isalnum() or NOS_API.test_cases_results_info.cas_id_using_barcode.isdigit())):
                CASID_LABEL = True

            if ((len(NOS_API.test_cases_results_info.mac_using_barcode) == MAC_LENGTH) and (NOS_API.test_cases_results_info.mac_using_barcode.isalnum() or NOS_API.test_cases_results_info.mac_using_barcode.isdigit())):
                MAC_LABEL = True
            
            if not(SN_LABEL and CASID_LABEL and MAC_LABEL):               
                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.scan_error_code \
                                               + "; Error message: " + NOS_API.test_cases_results_info.scan_error_message)
                NOS_API.set_error_message("Leitura de Etiquetas")
                error_codes = NOS_API.test_cases_results_info.scan_error_code
                error_messages = NOS_API.test_cases_results_info.scan_error_message            
                NOS_API.add_test_case_result_to_file_report(
                                test_result,
                                "- - - - - - - - - - - - - - - - - - - -",
                                "- - - - - - - - - - - - - - - - - - - -",
                                error_codes,
                                error_messages)
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                report_file = ""    
                if (test_result != "PASS"):
                    report_file = NOS_API.create_test_case_log_file(
                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                    NOS_API.test_cases_results_info.nos_sap_number,
                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                    end_time)
                    NOS_API.upload_file_report(report_file) 
                    NOS_API.test_cases_results_info.isTestOK = False
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                            test_result,
                            end_time,
                            error_codes,
                            report_file)
            
                ## Update test result
                TEST_CREATION_API.update_test_result(test_result)
            
                ## Return DUT to initial state and de-initialize grabber device
                NOS_API.deinitialize()
                return

            if(System_Failure == 0):
                if not(NOS_API.display_new_dialog("Conectores?", NOS_API.WAIT_TIME_TO_CLOSE_DIALOG) == "OK"):              
                    test_result = "FAIL"
                    TEST_CREATION_API.write_log_to_file("Conectores NOK")
                    NOS_API.set_error_message("Danos Externos")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.conector_nok_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.conector_nok_error_message)
                    error_codes = NOS_API.test_cases_results_info.conector_nok_error_code
                    error_messages = NOS_API.test_cases_results_info.conector_nok_error_message           

                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
            
            ###############################################################################################################################################
            ################################################################## AutoDiag Test ##############################################################
            ###############################################################################################################################################
            while (counter < ATTEMPT_OPEN_AUTODIAG):
                if (NOS_API.configure_power_switch_by_inspection()):
                    if not(NOS_API.power_off()):
                        TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                        
                        NOS_API.set_error_message("POWER SWITCH")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                        error_codes = NOS_API.test_cases_results_info.power_switch_error_code
                        error_messages = NOS_API.test_cases_results_info.power_switch_error_message
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        NOS_API.add_test_case_result_to_file_report(
                                test_result,
                                "- - - - - - - - - - - - - - - - - - - -",
                                "- - - - - - - - - - - - - - - - - - - -",
                                error_codes,
                                error_messages)
                    
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = NOS_API.create_test_case_log_file(
                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                    NOS_API.test_cases_results_info.nos_sap_number,
                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                    end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                            test_result,
                            end_time,
                            error_codes,
                            report_file)
                        
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                        
                        return  
                    time.sleep(2)
                else:
                    TEST_CREATION_API.write_log_to_file("Incorrect test place name")
                    
                    NOS_API.set_error_message("POWER SWITCH")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                        + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                    error_codes = NOS_API.test_cases_results_info.power_switch_error_code
                    error_messages = NOS_API.test_cases_results_info.power_switch_error_message
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    NOS_API.add_test_case_result_to_file_report(
                            test_result,
                            "- - - - - - - - - - - - - - - - - - - -",
                            "- - - - - - - - - - - - - - - - - - - -",
                            error_codes,
                            error_messages)
                
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                NOS_API.test_cases_results_info.nos_sap_number,
                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                NOS_API.test_cases_results_info.mac_using_barcode,
                                end_time)
                    NOS_API.upload_file_report(report_file)
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                        
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                   
                    return 
                if counter > 0:
                    NOS_API.send_command_uma_uma("down")
                    time.sleep(1)

                NOS_API.display_custom_dialog("Pressione bot\xe3o 'Power' e quando Led piscar largue bot\xe3o e volte a pressionar uma vez", 1, ["Continuar"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG)
                time.sleep(1)
                if not(NOS_API.power_on()):
                    TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                    
                    NOS_API.set_error_message("POWER SWITCH")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                        + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                    error_codes = NOS_API.test_cases_results_info.power_switch_error_code
                    error_messages = NOS_API.test_cases_results_info.power_switch_error_message
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    NOS_API.add_test_case_result_to_file_report(
                            test_result,
                            "- - - - - - - - - - - - - - - - - - - -",
                            "- - - - - - - - - - - - - - - - - - - -",
                            error_codes,
                            error_messages)
                
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                NOS_API.test_cases_results_info.nos_sap_number,
                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                NOS_API.test_cases_results_info.mac_using_barcode,
                                end_time)
                    NOS_API.upload_file_report(report_file)
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                   
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                   
                    return
                
                time.sleep(1)
                
                start_time = int(time.time())
                NOS_API.display_custom_dialog("", 1, ["Repetir"], WAIT_AUTODIAG_START)
                timeout = int(time.time()) - start_time
                
                if (counter == 0 and Grabber_Init == 0):
                    ## Initialize grabber device
                    NOS_API.initialize_grabber()
                    
                    ## Start grabber device with video on default video source
                    NOS_API.grabber_start_video_source(TEST_CREATION_API.VideoInterface.HDMI1)
                    ## Start grabber device with audio on default audio source
                    TEST_CREATION_API.grabber_start_audio_source(TEST_CREATION_API.AudioInterface.HDMI1)
                
                if (timeout >= WAIT_AUTODIAG_START):
                    AutoDiag_start = NOS_API.wait_for_multiple_pictures(["Menu_ref"], WAIT_AUTODIAG_TEST, ["[Menu]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                    if (AutoDiag_start == -2):
                        NOS_API.display_custom_dialog("Confirme o cabo HDMI", 1, ["Continuar"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG)
                        AutoDiag_start = NOS_API.wait_for_multiple_pictures(["Menu_ref"], 10, ["[Menu]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                        if (AutoDiag_start != -1 and AutoDiag_start != -2 ):
                            counter = 4
                            AutoDiag_Test = True
                            break
                        elif (AutoDiag_start == -2):
                            if (NOS_API.display_custom_dialog("A STB est\xe1 ligada?", 2, ["OK", "NOK"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG) == "OK"):   
                                TEST_CREATION_API.write_log_to_file("Image is not displayed on HDMI")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                                    + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                                NOS_API.set_error_message("Video HDMI(Não Retestar)")
                                error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                                error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                                NOS_API.add_test_case_result_to_file_report(
                                                test_result,
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                error_codes,
                                                error_messages)
                                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                report_file = ""    
                                if (test_result != "PASS"):
                                    report_file = NOS_API.create_test_case_log_file(
                                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                                    NOS_API.test_cases_results_info.nos_sap_number,
                                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                                    end_time)
                                    NOS_API.upload_file_report(report_file) 
                                    NOS_API.test_cases_results_info.isTestOK = False
                                    
                                    NOS_API.send_report_over_mqtt_test_plan(
                                            test_result,
                                            end_time,
                                            error_codes,
                                            report_file)
                                
                                ## Update test result
                                TEST_CREATION_API.update_test_result(test_result)
                                
                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                                return
                            else:
                                TEST_CREATION_API.write_log_to_file("No Power")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.no_power_error_code \
                                                                        + "; Error message: " + NOS_API.test_cases_results_info.no_power_error_message)
                                NOS_API.set_error_message("Não Liga")
                                error_codes = NOS_API.test_cases_results_info.no_power_error_code
                                error_messages = NOS_API.test_cases_results_info.no_power_error_message
                                NOS_API.add_test_case_result_to_file_report(
                                                test_result,
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                error_codes,
                                                error_messages)
                                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                report_file = ""    
                                if (test_result != "PASS"):
                                    report_file = NOS_API.create_test_case_log_file(
                                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                                    NOS_API.test_cases_results_info.nos_sap_number,
                                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                                    end_time)
                                    NOS_API.upload_file_report(report_file) 
                                    NOS_API.test_cases_results_info.isTestOK = False
                                    
                                    NOS_API.send_report_over_mqtt_test_plan(
                                            test_result,
                                            end_time,
                                            error_codes,
                                            report_file)
                                
                                ## Update test result
                                TEST_CREATION_API.update_test_result(test_result)
                                
                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                                return

                    elif (AutoDiag_start != -1 and AutoDiag_start != -2):
                        counter = 4
                        AutoDiag_Test = True
                    
                    ###############################################################################################################################################
                    ################################################################## Upgrade_Test ###############################################################
                    ###############################################################################################################################################
                    
                    if(AutoDiag_Test):    
                        ## Extracts STB Info and Checks STB Version and Upgrades if STB doesn't have current software
                        NOS_API.send_command_uma_uma("down,down,ok")
                        
                        if not(NOS_API.grab_picture("ProductInformation")):
                            TEST_CREATION_API.write_log_to_file("HDMI NOK")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                            NOS_API.set_error_message("Video HDMI")
                            error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                            error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                            
                            NOS_API.add_test_case_result_to_file_report(
                                            test_result,
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            error_codes,
                                            error_messages)
                            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            report_file = ""    
                            if (test_result != "PASS"):
                                report_file = NOS_API.create_test_case_log_file(
                                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                                NOS_API.test_cases_results_info.nos_sap_number,
                                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                NOS_API.test_cases_results_info.mac_using_barcode,
                                                end_time)
                                NOS_API.upload_file_report(report_file) 
                                NOS_API.test_cases_results_info.isTestOK = False
                                
                                NOS_API.send_report_over_mqtt_test_plan(
                                        test_result,
                                        end_time,
                                        error_codes,
                                        report_file)
                        
                            ## Update test result
                            TEST_CREATION_API.update_test_result(test_result)
                        
                            ## Return DUT to initial state and de-initialize grabber device
                            NOS_API.deinitialize()
                            return
                        if not(TEST_CREATION_API.compare_pictures("Product_Information_ref", "ProductInformation", "[Product_Information]")):
                            NOS_API.send_command_uma_uma("back,up,up,up")
                            NOS_API.send_command_uma_uma("down,down,ok")
                            if not(NOS_API.grab_picture("ProductInformationScnd")):
                                TEST_CREATION_API.write_log_to_file("HDMI NOK")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                        + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                                NOS_API.set_error_message("Video HDMI")
                                error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                                error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                                
                                NOS_API.add_test_case_result_to_file_report(
                                                test_result,
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                error_codes,
                                                error_messages)
                                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                report_file = ""    
                                if (test_result != "PASS"):
                                    report_file = NOS_API.create_test_case_log_file(
                                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                                    NOS_API.test_cases_results_info.nos_sap_number,
                                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                                    end_time)
                                    NOS_API.upload_file_report(report_file) 
                                    NOS_API.test_cases_results_info.isTestOK = False
                                    
                                    NOS_API.send_report_over_mqtt_test_plan(
                                            test_result,
                                            end_time,
                                            error_codes,
                                            report_file)
                            
                                ## Update test result
                                TEST_CREATION_API.update_test_result(test_result)
                            
                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                                return
                            if not(TEST_CREATION_API.compare_pictures("Product_Information_ref", "ProductInformationScnd", "[Product_Information]")):
                                TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                                NOS_API.set_error_message("Navegação")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                        + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                                error_codes = NOS_API.test_cases_results_info.navigation_error_code
                                error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                                
                                NOS_API.add_test_case_result_to_file_report(
                                            test_result,
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            error_codes,
                                            error_messages)
                                
                                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                report_file = ""    
                                
                                report_file = NOS_API.create_test_case_log_file(
                                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                                NOS_API.test_cases_results_info.nos_sap_number,
                                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                NOS_API.test_cases_results_info.mac_using_barcode,
                                                end_time)
                                NOS_API.upload_file_report(report_file)
                                
                                NOS_API.send_report_over_mqtt_test_plan(
                                        test_result,
                                        end_time,
                                        error_codes,
                                        report_file)

                                ## Update test result
                                TEST_CREATION_API.update_test_result(test_result)

                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                                return
                        
                        if not(NOS_API.grab_picture("ProductInformation")):
                            TEST_CREATION_API.write_log_to_file("HDMI NOK")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                            NOS_API.set_error_message("Video HDMI")
                            error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                            error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                            
                            NOS_API.add_test_case_result_to_file_report(
                                            test_result,
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            error_codes,
                                            error_messages)
                            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            report_file = ""    
                            if (test_result != "PASS"):
                                report_file = NOS_API.create_test_case_log_file(
                                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                                NOS_API.test_cases_results_info.nos_sap_number,
                                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                NOS_API.test_cases_results_info.mac_using_barcode,
                                                end_time)
                                NOS_API.upload_file_report(report_file) 
                                NOS_API.test_cases_results_info.isTestOK = False
                                
                                NOS_API.send_report_over_mqtt_test_plan(
                                        test_result,
                                        end_time,
                                        error_codes,
                                        report_file)
                        
                            ## Update test result
                            TEST_CREATION_API.update_test_result(test_result)
                        
                            ## Return DUT to initial state and de-initialize grabber device
                            NOS_API.deinitialize()
                            return
                        SN_Number = NOS_API.remove_whitespaces(TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[SN_Number]", "[AUTODIAG_FILTER]", "SN_Number"))
                        SN_Number = NOS_API.Fix_SN_UMA_UMA(SN_Number)
                        Software_Version = TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[Software_Version]", "[AUTODIAG_FILTER]", "Software_Version")
                        NOS_API.test_cases_results_info.firmware_version = Software_Version
                        AutoDiag_Version = TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[AutoDiag_Version]", "[AUTODIAG_FILTER]", "AutoDiag_Version")
                        CAS_ID = TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[CAS_ID]", "[AUTODIAG_FILTER]", "CAS_ID")
                        NOS_API.test_cases_results_info.cas_id_number = CAS_ID
                        Eth_MAC = TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[Eth_MAC]", "[AUTODIAG_FILTER]", "Eth_MAC")
                        Eth_MAC = NOS_API.fix_mac_stb_uma_uma(Eth_MAC)
                        WiFi_MAC = TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[WiFi_MAC]", "[AUTODIAG_FILTER]", "WiFi_MAC")
                        WiFi_MAC = NOS_API.fix_mac_stb_uma_uma(WiFi_MAC)
                        WiFi_Firmware = TEST_CREATION_API.OCR_recognize_text("ProductInformation", "[WiFi_Firmware]", "[AUTODIAG_FILTER]", "WiFi_Firmware") 
                                                
                        if Software_Version == NOS_API.Firmware_Version_ZC4430KNO:
                            counter = 4
                            Upgrade_Test = True
                            if NOS_API.test_cases_results_info.DidUpgrade == 1:
                                TEST_CREATION_API.write_log_to_file("Atualização: OK") 
                            else:
                                TEST_CREATION_API.write_log_to_file("Atualização: N/A") 
                            break
                        else: 
                            if NOS_API.test_cases_results_info.DidUpgrade == 1:
                                Upgrade_Tries = 2
                                counter = 4
                                TEST_CREATION_API.write_log_to_file("Atualização: NOK") 
                                TEST_CREATION_API.write_log_to_file("Doesn't upgrade")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.upgrade_nok_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.upgrade_nok_error_message)                                        
                                NOS_API.set_error_message("Não Actualiza") 
                                error_codes =  NOS_API.test_cases_results_info.upgrade_nok_error_code
                                error_messages = NOS_API.test_cases_results_info.upgrade_nok_error_message
       
                            while Upgrade_Tries < 2:
                                NOS_API.configure_power_switch_by_inspection()
                                if not(NOS_API.power_off()):
                                    TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                                       
                                    NOS_API.set_error_message("POWER SWITCH")
                                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                                        + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                                    error_codes = NOS_API.test_cases_results_info.power_switch_error_code
                                    error_messages = NOS_API.test_cases_results_info.power_switch_error_message
                                    ## Return DUT to initial state and de-initialize grabber device
                                    NOS_API.deinitialize()
                                    NOS_API.add_test_case_result_to_file_report(
                                            test_result,
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            error_codes,
                                            error_messages)
                                   
                                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    report_file = NOS_API.create_test_case_log_file(
                                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                                NOS_API.test_cases_results_info.nos_sap_number,
                                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                NOS_API.test_cases_results_info.mac_using_barcode,
                                                end_time)
                                    NOS_API.upload_file_report(report_file)
                                       
                                    NOS_API.send_report_over_mqtt_test_plan(
                                        test_result,
                                        end_time,
                                        error_codes,
                                        report_file)
                                       
                                    ## Update test result
                                    TEST_CREATION_API.update_test_result(test_result)
                                       
                                    return
                                NOS_API.send_command_uma_uma("down")
                                time.sleep(1)
                                NOS_API.display_custom_dialog("Pressione bot\xe3o 'Power' at\xe9 fixar led roxo", 1, ["Continuar"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG)
                                time.sleep(1)
                                
                                if not(NOS_API.power_on()):
                                    TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                                    ## Update test result
                                    TEST_CREATION_API.update_test_result(test_result)
                                    NOS_API.set_error_message("Inspection")
                                
                                    NOS_API.add_test_case_result_to_file_report(
                                                    test_result,
                                                    "- - - - - - - - - - - - - - - - - - - -",
                                                    "- - - - - - - - - - - - - - - - - - - -",
                                                    error_codes,
                                                    error_messages)
                                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')    
                                    report_file = ""
                                    if (test_result != "PASS"):
                                        report_file = NOS_API.create_test_case_log_file(
                                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                                        NOS_API.test_cases_results_info.nos_sap_number,
                                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                        "",
                                                        end_time)
                                        NOS_API.upload_file_report(report_file)
                                        NOS_API.test_cases_results_info.isTestOK = False
                                
                                
                                    ## Return DUT to initial state and de-initialize grabber device
                                    NOS_API.deinitialize()
                                
                                    NOS_API.send_report_over_mqtt_test_plan(
                                            test_result,
                                            end_time,
                                            error_codes,
                                            report_file)
                                
                                    return
                                 
                                ##Upgrade_Start = NOS_API.wait_for_multiple_pictures(["Upgrade_ref"], 55, ["[Upgrade_Logo]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                                Upgrade_Start = NOS_API.wait_for_multiple_pictures(["Upgrade_ref"], 120, ["[Upgrade_Logo]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                                
                                if Upgrade_Start == -2 or Upgrade_Start == -1:
                                    Upgrade_Tries += 1
                                    continue
                                else:
                                    time.sleep(4)
                                    if(NOS_API.wait_for_no_signal_present(Upgrade_Time)):
                                        NOS_API.test_cases_results_info.DidUpgrade = 1
                                        Upgrade_Tries = 3
                                    else:
                                        Upgrade_Tries += 1
                                        continue
                            
                            if Upgrade_Tries == 3:
                                counter = 0
                                Grabber_Init = 1
                                continue
                            else:
                                TEST_CREATION_API.write_log_to_file("Atualização: NOK") 
                                TEST_CREATION_API.write_log_to_file("Doesn't upgrade")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.upgrade_nok_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.upgrade_nok_error_message)                                        
                                NOS_API.set_error_message("Não Actualiza") 
                                error_codes =  NOS_API.test_cases_results_info.upgrade_nok_error_code
                                error_messages = NOS_API.test_cases_results_info.upgrade_nok_error_message

                                NOS_API.add_test_case_result_to_file_report(
                                                test_result,
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                error_codes,
                                                error_messages)
                                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                report_file = ""    
                                if (test_result != "PASS"):
                                    report_file = NOS_API.create_test_case_log_file(
                                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                                    NOS_API.test_cases_results_info.nos_sap_number,
                                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                                    end_time)
                                    NOS_API.upload_file_report(report_file) 
                                    NOS_API.test_cases_results_info.isTestOK = False
                                    
                                    NOS_API.send_report_over_mqtt_test_plan(
                                            test_result,
                                            end_time,
                                            error_codes,
                                            report_file)
                            
                                ## Update test result
                                TEST_CREATION_API.update_test_result(test_result)
                            
                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                                return
                                
                counter = counter + 1
                
            if (counter == 3):
                TEST_CREATION_API.write_log_to_file("Autodiag failed")
                NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.autodiag_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.autodiag_error_message)
                NOS_API.set_error_message("AutoDiag")
                error_codes = NOS_API.test_cases_results_info.autodiag_error_code
                error_messages = NOS_API.test_cases_results_info.autodiag_error_message
                
            ###############################################################################################################################################
            ################################################################## STB_Info_Test ##############################################################
            ###############################################################################################################################################

            if (Upgrade_Test):
                ## Compares STB Info with with Info given by labels read by operators
                if (NOS_API.ignore_zero_letter_o_during_comparation(NOS_API.test_cases_results_info.s_n_using_barcode, SN_Number)):
                    if (NOS_API.ignore_zero_letter_o_during_comparation(NOS_API.test_cases_results_info.cas_id_using_barcode, CAS_ID)):
                        if (NOS_API.test_cases_results_info.mac_using_barcode == Eth_MAC):
                            TEST_CREATION_API.write_log_to_file("########## STB Info ##########")
                            TEST_CREATION_API.write_log_to_file("Serial Number: " + str(SN_Number))
                            TEST_CREATION_API.write_log_to_file("CAS ID: " + str(CAS_ID))
                            TEST_CREATION_API.write_log_to_file("Eth MAC: " + str(Eth_MAC))
                            TEST_CREATION_API.write_log_to_file("WiFi MAC: " + str(WiFi_MAC))
                            TEST_CREATION_API.write_log_to_file("Software Version: " + str(Software_Version))
                            TEST_CREATION_API.write_log_to_file("AutoDiag Version: " + str(AutoDiag_Version))
                            TEST_CREATION_API.write_log_to_file("WiFi Firmware: " + str(WiFi_Firmware)) 
                            TEST_CREATION_API.write_log_to_file("\n")
                            ###################################################################################################################
                            ################################################## Ethernet Test ##################################################
                            ###################################################################################################################

                            slot = NOS_API.slot_index(NOS_API.get_test_place_name())
                            if NOS_API.Check_Eth_Port_UMA_UMA(slot, Eth_MAC):
                                STB_Info_Test = True
                            else:
                                TEST_CREATION_API.write_log_to_file("Ethernet Test Fails")
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.ethernet_nok_error_code \
                                                        + "; Error message: " + NOS_API.test_cases_results_info.ethernet_nok_error_message)
                                NOS_API.set_error_message("Eth")
                                error_codes = NOS_API.test_cases_results_info.ethernet_nok_error_code
                                error_messages = NOS_API.test_cases_results_info.ethernet_nok_error_message
                                test_result = "FAIL"    
                        else:
                            TEST_CREATION_API.write_log_to_file("CM MAC number(" + str(Eth_MAC) + ") and CM MAC number previuosly scanned(" + str(NOS_API.test_cases_results_info.mac_using_barcode) + ") is not the same")
                            NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.wrong_mac_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.wrong_mac_error_message)
                            NOS_API.set_error_message("MAC")
                            error_codes = NOS_API.test_cases_results_info.wrong_mac_error_code
                            error_messages = NOS_API.test_cases_results_info.wrong_mac_error_message
                    else:
                        TEST_CREATION_API.write_log_to_file("CAS ID number(" + str(CAS_ID) + ") and CAS ID number previuosly scanned(" + str(NOS_API.test_cases_results_info.cas_id_using_barcode) + ") is not the same")
                        NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.wrong_cas_id_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.wrong_cas_id_error_message \
                                                            + "; OCR: " + str(CAS_ID))
                        NOS_API.set_error_message("CAS ID")
                        error_codes = NOS_API.test_cases_results_info.wrong_cas_id_error_code
                        error_messages = NOS_API.test_cases_results_info.wrong_cas_id_error_message
                else:
                    TEST_CREATION_API.write_log_to_file("Logistic serial number(" + str(SN_Number) + ") is not the same as scanned serial number(" + str(NOS_API.test_cases_results_info.s_n_using_barcode) + ")")        
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.wrong_s_n_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.wrong_s_n_error_message \
                                                            + "; OCR: " + str(SN_Number))
                    NOS_API.set_error_message("S/N")
                    error_codes = NOS_API.test_cases_results_info.wrong_s_n_error_code
                    error_messages = NOS_API.test_cases_results_info.wrong_s_n_error_message
            
            ###############################################################################################################################################
            ################################################################## WiFi Test ##################################################################
            ###############################################################################################################################################
            
            if (STB_Info_Test):
                NOS_API.send_command_uma_uma("back,up,ok")
                if not(NOS_API.grab_picture("WiFi_Menu")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("WiFi_ref", "WiFi_Menu", "[WiFi_Menu]")):
                    NOS_API.send_command_uma_uma("back,up,up,up")
                    NOS_API.send_command_uma_uma("down,ok")
                    if not(NOS_API.grab_picture("WiFi_MenuScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("WiFi_ref", "WiFi_MenuScn", "[WiFi_Menu]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                NOS_API.send_command_uma_uma("ok")
                
                WiFi_24G = NOS_API.wait_for_multiple_pictures(["WiFi_OK_24G_ref"], 100, ["[AutoDiag_24G]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                
                if WiFi_24G != 0 and WiFi_24G != -2:
                    NOS_API.send_command_uma_uma("ok")
                    WiFi_24G = NOS_API.wait_for_multiple_pictures(["WiFi_OK_24G_ref"], 100, ["[AutoDiag_24G]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                
                if WiFi_24G == 0:
                    if not(NOS_API.grab_picture("WiFi_24G")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    
                    RSSI_24G = TEST_CREATION_API.OCR_recognize_text("WiFi_24G", "[RSSI]", "[AUTODIAG_FILTER]", "RSSI_24G")
                    WiFi_24G_MAC = TEST_CREATION_API.OCR_recognize_text("WiFi_24G", "[MAC]", "[AUTODIAG_FILTER]", "WiFi_24G_MAC")
                    WiFi_24G_MAC = NOS_API.fix_mac_stb_uma_uma(WiFi_24G_MAC)
                    IP_24G = TEST_CREATION_API.OCR_recognize_text("WiFi_24G", "[IP]", "[AUTODIAG_FILTER]", "IP_24G")
                    IP_24G = NOS_API.Fix_IP_UMA_UMA(IP_24G)
                    
                    TEST_CREATION_API.write_log_to_file("########## WiFi_24G Info ##########")
                    TEST_CREATION_API.write_log_to_file("RSSI: " + str(RSSI_24G))
                    TEST_CREATION_API.write_log_to_file("WiFi 2.4G MAC: " + str(WiFi_24G_MAC))
                    TEST_CREATION_API.write_log_to_file("WiFi 2.4G IP: " + str(IP_24G))
                    TEST_CREATION_API.write_log_to_file("\n")
                    
                    NOS_API.send_command_uma_uma("right,ok")
                    time.sleep(1)
                    NOS_API.send_command_uma_uma("ok")
                    
                    WiFi_5G = NOS_API.wait_for_multiple_pictures(["WiFi_OK_5G_ref"], 100, ["[AutoDiag_5G]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                    
                    if WiFi_5G != 0 and WiFi_5G != -2:
                        NOS_API.send_command_uma_uma("ok")
                        WiFi_5G = NOS_API.wait_for_multiple_pictures(["WiFi_OK_5G_ref"], 100, ["[AutoDiag_5G]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                    
                    if WiFi_5G == 0:
                        if not(NOS_API.grab_picture("WiFi_5G")):
                            TEST_CREATION_API.write_log_to_file("HDMI NOK")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                            NOS_API.set_error_message("Video HDMI")
                            error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                            error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                            
                            NOS_API.add_test_case_result_to_file_report(
                                            test_result,
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            error_codes,
                                            error_messages)
                            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            report_file = ""    
                            if (test_result != "PASS"):
                                report_file = NOS_API.create_test_case_log_file(
                                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                                NOS_API.test_cases_results_info.nos_sap_number,
                                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                NOS_API.test_cases_results_info.mac_using_barcode,
                                                end_time)
                                NOS_API.upload_file_report(report_file) 
                                NOS_API.test_cases_results_info.isTestOK = False
                                
                                NOS_API.send_report_over_mqtt_test_plan(
                                        test_result,
                                        end_time,
                                        error_codes,
                                        report_file)
                        
                            ## Update test result
                            TEST_CREATION_API.update_test_result(test_result)
                        
                            ## Return DUT to initial state and de-initialize grabber device
                            NOS_API.deinitialize()
                            return
                    
                        RSSI_5G = TEST_CREATION_API.OCR_recognize_text("WiFi_5G", "[RSSI]", "[AUTODIAG_FILTER]", "RSSI_5G")
                        WiFi_5G_MAC = TEST_CREATION_API.OCR_recognize_text("WiFi_5G", "[MAC]", "[AUTODIAG_FILTER]", "WiFi_5G_MAC")
                        WiFi_5G_MAC = NOS_API.fix_mac_stb_uma_uma(WiFi_5G_MAC)
                        IP_5G = TEST_CREATION_API.OCR_recognize_text("WiFi_5G", "[IP]", "[AUTODIAG_FILTER]", "IP_5G")
                        IP_5G = NOS_API.Fix_IP_UMA_UMA(IP_5G)
                        
                        TEST_CREATION_API.write_log_to_file("########## WiFi_5G Info ##########")
                        TEST_CREATION_API.write_log_to_file("RSSI: " + str(RSSI_5G))
                        TEST_CREATION_API.write_log_to_file("WiFi 5G MAC: " + str(WiFi_5G_MAC))
                        TEST_CREATION_API.write_log_to_file("WiFi 5G IP: " + str(IP_5G))
                        TEST_CREATION_API.write_log_to_file("\n")
                        
                        WiFi_Test = True
                    else:
                        if WiFi_24G == -2:
                            TEST_CREATION_API.write_log_to_file("STB lost Signal.Possible Reboot.")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.reboot_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.reboot_error_message)
                            NOS_API.set_error_message("Reboot")
                            error_codes = NOS_API.test_cases_results_info.reboot_error_code
                            error_messages = NOS_API.test_cases_results_info.reboot_error_message
                            test_result = "FAIL"
                        else:
                            TEST_CREATION_API.write_log_to_file("STB didn't connect to AutoDiag_5G WiFi")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.wifi_5g_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.wifi_5g_error_message)
                            NOS_API.set_error_message("WiFi")
                            error_codes = NOS_API.test_cases_results_info.wifi_5g_error_code
                            error_messages = NOS_API.test_cases_results_info.wifi_5g_error_message
                            test_result = "FAIL"
                else:
                    if WiFi_24G == -2:
                        TEST_CREATION_API.write_log_to_file("STB lost Signal.Possible Reboot.")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.reboot_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.reboot_error_message)
                        NOS_API.set_error_message("Reboot")
                        error_codes = NOS_API.test_cases_results_info.reboot_error_code
                        error_messages = NOS_API.test_cases_results_info.reboot_error_message
                        test_result = "FAIL"
                    else:
                        TEST_CREATION_API.write_log_to_file("STB didn't connect to AutoDiag_24G WiFi")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.wifi_24g_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.wifi_24g_error_message)
                        NOS_API.set_error_message("WiFi")
                        error_codes = NOS_API.test_cases_results_info.wifi_24g_error_code
                        error_messages = NOS_API.test_cases_results_info.wifi_24g_error_message
                        test_result = "FAIL"
            
            ###############################################################################################################################################
            ################################################################## Front Panel Test ###########################################################
            ###############################################################################################################################################
            if(WiFi_Test):
                NOS_API.send_command_uma_uma("back,down,down,ok,down,ok")
                if not(NOS_API.grab_picture("Front_Panel")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Front_Panel_Menu_ref", "Front_Panel", "[Front_Panel]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,ok,down,ok")
                    if not(NOS_API.grab_picture("Front_PanelScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Front_Panel_Menu_ref", "Front_PanelScn", "[Front_Panel]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                if (NOS_API.display_custom_dialog("O Led Vermelho e azul est\xe3o a piscar?", 2, ["OK", "NOK"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG) == "OK"):
                    Front_Panel = True
                else:
                    TEST_CREATION_API.write_log_to_file("Led Power NOK.")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.led_power_nok_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.led_power_nok_error_message)
                    NOS_API.set_error_message("Led's")
                    error_codes = NOS_API.test_cases_results_info.led_power_nok_error_code
                    error_messages = NOS_API.test_cases_results_info.led_power_nok_error_message
                    test_result = "FAIL"
            
            ###############################################################################################################################################
            ################################################################## Equipment Test #############################################################
            ###############################################################################################################################################
            if(Front_Panel):
                NOS_API.send_command_uma_uma("back,back,down,ok")
                if not(NOS_API.grab_picture("Equipment")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Equipment_Menu_ref", "Equipment", "[Equipment]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,ok,down,ok")
                    if not(NOS_API.grab_picture("EquipmentScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Equipment_Menu_ref", "EquipmentScn", "[Equipment]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                if not(NOS_API.grab_picture("Equipment")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
             
                if (TEST_CREATION_API.compare_pictures("Equipment_Menu_ref", "Equipment", "[WiFi]")):
                    if (TEST_CREATION_API.compare_pictures("Equipment_Menu_ref", "Equipment", "[Flash]")):
                        CPU_Temperature = NOS_API.remove_whitespaces(TEST_CREATION_API.OCR_recognize_text("Equipment", "[Temperature]", "[AUTODIAG_FILTER]", "CPU_Temperature"))
                        CPU_Temperature_Fixed = NOS_API.Fix_Temperature_UMA_UMA(CPU_Temperature)
                        if CPU_Temperature_Fixed > CPU_Temperature_Threshold:
                            TEST_CREATION_API.write_log_to_file("########## Equipment Results ##########")
                            TEST_CREATION_API.write_log_to_file("WiFi Test: OK")
                            TEST_CREATION_API.write_log_to_file("Flash Test: OK")
                            TEST_CREATION_API.write_log_to_file("CPU Temperature: " + str(CPU_Temperature))
                            TEST_CREATION_API.write_log_to_file("\n")
                            Equipment_Test = True
                        else:
                            TEST_CREATION_API.write_log_to_file("CPU Temperature(" + str(CPU_Temperature_Fixed) + ") is bigger than Threshold(" + str(CPU_Temperature_Threshold) + ")")
                            NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.cpu_temp_nok_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.cpu_temp_nok_error_message)
                            NOS_API.set_error_message("IC")
                            error_codes = NOS_API.test_cases_results_info.cpu_temp_nok_error_code
                            error_messages = NOS_API.test_cases_results_info.cpu_temp_nok_error_message
                    else:
                        TEST_CREATION_API.write_log_to_file("Flash Test Fails")
                        NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.flash_nok_error_code \
                                                        + "; Error message: " + NOS_API.test_cases_results_info.flash_nok_error_message)
                        NOS_API.set_error_message("IC")
                        error_codes = NOS_API.test_cases_results_info.flash_nok_error_code
                        error_messages = NOS_API.test_cases_results_info.flash_nok_error_message
                else:
                    TEST_CREATION_API.write_log_to_file("STB didn't connect to AutoDiag_24G WiFi")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.wifi_24g_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.wifi_24g_error_message)
                    NOS_API.set_error_message("WiFi")
                    error_codes = NOS_API.test_cases_results_info.wifi_24g_error_code
                    error_messages = NOS_API.test_cases_results_info.wifi_24g_error_message
                    test_result = "FAIL"
            
            ###############################################################################################################################################
            ################################################################## Peripherals Test #############################################################
            ###############################################################################################################################################
            if(Equipment_Test):
                NOS_API.send_command_uma_uma("back,down,ok")
                if not(NOS_API.grab_picture("Peripherals")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "Peripherals", "[Peripherals]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,down,down,ok")
                    if not(NOS_API.grab_picture("PeripheralsScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "PeripheralsScn", "[Peripherals]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    
                if not(NOS_API.grab_picture("Peripherals")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                
                if (TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "Peripherals", "[USB]")):
                    #if (TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "Peripherals", "[Eth]")):
                    if (TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "Peripherals", "[HDMI]")):
                        TEST_CREATION_API.write_log_to_file("########## Peripherals Results ##########")
                        TEST_CREATION_API.write_log_to_file("USB Test: OK")
                        TEST_CREATION_API.write_log_to_file("Ethernet Test: OK")
                        TEST_CREATION_API.write_log_to_file("HDMI Test: OK")
                        Peripherals_Test = True
                    else:
                        TEST_CREATION_API.write_log_to_file("HDMI Test Fails")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.hdmi_test_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.hdmi_test_error_message)
                        NOS_API.set_error_message("WiFi")
                        error_codes = NOS_API.test_cases_results_info.hdmi_test_error_code
                        error_messages = NOS_API.test_cases_results_info.hdmi_test_error_message
                        test_result = "FAIL"
                    # else:
                    #     NOS_API.display_custom_dialog("Verifique cabo Ethernet", 1, ["Continuar"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG)
                    #     time.sleep(1)
                    #     if not(NOS_API.grab_picture("Peripherals2Try")):
                    #         TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    #         NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                    #                                 + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    #         NOS_API.set_error_message("Video HDMI")
                    #         error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    #         error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                            
                    #         NOS_API.add_test_case_result_to_file_report(
                    #                         test_result,
                    #                         "- - - - - - - - - - - - - - - - - - - -",
                    #                         "- - - - - - - - - - - - - - - - - - - -",
                    #                         error_codes,
                    #                         error_messages)
                    #         end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    #         report_file = ""    
                    #         if (test_result != "PASS"):
                    #             report_file = NOS_API.create_test_case_log_file(
                    #                             NOS_API.test_cases_results_info.s_n_using_barcode,
                    #                             NOS_API.test_cases_results_info.nos_sap_number,
                    #                             NOS_API.test_cases_results_info.cas_id_using_barcode,
                    #                             NOS_API.test_cases_results_info.mac_using_barcode,
                    #                             end_time)
                    #             NOS_API.upload_file_report(report_file) 
                    #             NOS_API.test_cases_results_info.isTestOK = False
                                
                    #             NOS_API.send_report_over_mqtt_test_plan(
                    #                     test_result,
                    #                     end_time,
                    #                     error_codes,
                    #                     report_file)
                        
                    #         ## Update test result
                    #         TEST_CREATION_API.update_test_result(test_result)
                        
                    #         ## Return DUT to initial state and de-initialize grabber device
                    #         NOS_API.deinitialize()
                    #         return
                
                    #     if (TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "Peripherals2Try", "[Eth]")):
                    #         if (TEST_CREATION_API.compare_pictures("Peripherals_Menu_ref", "Peripherals2Try", "[HDMI]")):
                    #             TEST_CREATION_API.write_log_to_file("########## Peripherals Results ##########")
                    #             TEST_CREATION_API.write_log_to_file("USB Test: OK")
                    #             TEST_CREATION_API.write_log_to_file("Ethernet Test: OK")
                    #             TEST_CREATION_API.write_log_to_file("HDMI Test: OK")
                    #             TEST_CREATION_API.write_log_to_file("\n")
                    #             Peripherals_Test = True
                    #         else:
                    #             TEST_CREATION_API.write_log_to_file("HDMI Test Fails")
                    #             NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.hdmi_test_error_code \
                    #                                     + "; Error message: " + NOS_API.test_cases_results_info.hdmi_test_error_message)
                    #             NOS_API.set_error_message("WiFi")
                    #             error_codes = NOS_API.test_cases_results_info.hdmi_test_error_code
                    #             error_messages = NOS_API.test_cases_results_info.hdmi_test_error_message
                    #             test_result = "FAIL"
                    #     else:
                    #         TEST_CREATION_API.write_log_to_file("Ethernet Test Fails")
                    #         NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.ethernet_nok_error_code \
                    #                                 + "; Error message: " + NOS_API.test_cases_results_info.ethernet_nok_error_message)
                    #         NOS_API.set_error_message("Eth")
                    #         error_codes = NOS_API.test_cases_results_info.ethernet_nok_error_code
                    #         error_messages = NOS_API.test_cases_results_info.ethernet_nok_error_message
                    #         test_result = "FAIL"
                else:
                    TEST_CREATION_API.write_log_to_file("USB Test Fails")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.usb_nok_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.usb_nok_error_message)
                    NOS_API.set_error_message("USB")
                    error_codes = NOS_API.test_cases_results_info.usb_nok_error_code
                    error_messages = NOS_API.test_cases_results_info.usb_nok_error_message
                    test_result = "FAIL"
             
            ###############################################################################################################################################
            ################################################################## Bluetooth Test #############################################################
            ###############################################################################################################################################
            if(Peripherals_Test):
                NOS_API.send_command_uma_uma("back,down,down,down,down,down,down,ok")
                if not(NOS_API.grab_picture("Bluetooth")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Bluetooth_Menu_ref", "Bluetooth", "[Bluetooth]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up,up,up,up,up,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,down,down,down,down,down,down,down,down,ok")
                    if not(NOS_API.grab_picture("BluetoothScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Bluetooth_Menu_ref", "BluetoothScn", "[Bluetooth]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                while BluetoothTries < BluetoothTriesThreshold:
                    NOS_API.send_command_uma_uma("ok")
                    
                    Bluetooth_Search = NOS_API.wait_for_multiple_pictures(["Bluetooth_Menu_ref"], 25, ["[Idle_Bluetooth]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                    
                    if Bluetooth_Search != -1 and Bluetooth_Search != -2:
                        if not(NOS_API.grab_picture("Bluetooth_" + str(BluetoothTries))):
                            TEST_CREATION_API.write_log_to_file("HDMI NOK")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                            NOS_API.set_error_message("Video HDMI")
                            error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                            error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                            
                            NOS_API.add_test_case_result_to_file_report(
                                            test_result,
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            "- - - - - - - - - - - - - - - - - - - -",
                                            error_codes,
                                            error_messages)
                            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            report_file = ""    
                            if (test_result != "PASS"):
                                report_file = NOS_API.create_test_case_log_file(
                                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                                NOS_API.test_cases_results_info.nos_sap_number,
                                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                NOS_API.test_cases_results_info.mac_using_barcode,
                                                end_time)
                                NOS_API.upload_file_report(report_file) 
                                NOS_API.test_cases_results_info.isTestOK = False
                                
                                NOS_API.send_report_over_mqtt_test_plan(
                                        test_result,
                                        end_time,
                                        error_codes,
                                        report_file)
                        
                            ## Update test result
                            TEST_CREATION_API.update_test_result(test_result)
                        
                            ## Return DUT to initial state and de-initialize grabber device
                            NOS_API.deinitialize()
                            return
                        
                        Position_One = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P1]", "[AUTODIAG_FILTER]", "BluetoothPosition1")) 
                        Position_Two = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P2]", "[AUTODIAG_FILTER]", "BluetoothPosition2"))
                        Position_Three = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P3]", "[AUTODIAG_FILTER]", "BluetoothPosition3"))
                        Position_Four = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P4]", "[AUTODIAG_FILTER]", "BluetoothPosition4"))
                        Position_Five = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P5]", "[AUTODIAG_FILTER]", "BluetoothPosition5"))
                        Position_Six = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P6]", "[AUTODIAG_FILTER]", "BluetoothPosition6"))
                        Position_Seven = NOS_API.Fix_Bluetooth_UMA_UMA(TEST_CREATION_API.OCR_recognize_text("Bluetooth_" + str(BluetoothTries), "[Bluetooth_P7]", "[AUTODIAG_FILTER]", "BluetoothPosition7"))
                        
                        for bluetooth in range(7):
                            if Position_One == "RACK" + str(bluetooth + 1) or Position_Two == "RACK" + str(bluetooth + 1) or Position_Three == "RACK" + str(bluetooth + 1) or Position_Four == "RACK" + str(bluetooth + 1) or Position_Five == "RACK" + str(bluetooth + 1) or Position_Six == "RACK" + str(bluetooth + 1) or Position_Seven == "RACK" + str(bluetooth + 1):
                                Bluetooth_Test = True
                                BluetoothTries = BluetoothTriesThreshold
                                TEST_CREATION_API.write_log_to_file("########## Bluetooth Result ##########")
                                TEST_CREATION_API.write_log_to_file("Bluetooth Test: OK")
                                TEST_CREATION_API.write_log_to_file("Bluetooth Device Detected: RACK" + str(bluetooth + 1))
                                TEST_CREATION_API.write_log_to_file("\n")
                                break
                    elif Bluetooth_Search == -2:
                        BluetoothTries = BluetoothTriesThreshold
                        TEST_CREATION_API.write_log_to_file("STB lost Signal.Possible Reboot.")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.reboot_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.reboot_error_message)
                        NOS_API.set_error_message("Reboot")
                        error_codes = NOS_API.test_cases_results_info.reboot_error_code
                        error_messages = NOS_API.test_cases_results_info.reboot_error_message
                        test_result = "FAIL"
                    
                    BluetoothTries += 1
                   
                if not(Bluetooth_Test):
                    TEST_CREATION_API.write_log_to_file("STB didn't detect any bluetooth device")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.bluetooth_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.bluetooth_error_message)
                    NOS_API.set_error_message("Bluetooth")
                    error_codes = NOS_API.test_cases_results_info.bluetooth_error_code
                    error_messages = NOS_API.test_cases_results_info.bluetooth_error_message
                    test_result = "FAIL"
             
            ###############################################################################################################################################
            ################################################################ HDMI HD 1080 Test ############################################################
            ###############################################################################################################################################
            if(Bluetooth_Test):
                ## Initialize PQM Test variable as True
                pqm_analyse_check = True   
                
                NOS_API.send_command_uma_uma("back,up,up,up,up,ok")
                if not(NOS_API.grab_picture("Sintonization")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Sintonization_Menu_ref", "Sintonization", "[Sintonization]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up,up,up,up,up,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,down,down,down,down,ok")
                    if not(NOS_API.grab_picture("SintonizationScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Sintonization_Menu_ref", "SintonizationScn", "[Sintonization]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                NOS_API.send_command_uma_uma("7,1,4,ok,down,6,8,7,5,ok,down,right,down,down,5,1,8,4,ok,down,right,right,down,5,1,8,5,ok,down,left,down,5,1,8,4,ok,play")
                time.sleep(1)
                
                if not (NOS_API.is_signal_present_on_video_source()):
                    TEST_CREATION_API.write_log_to_file("STB lost Signal.Possible Reboot.")
                    
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.reboot_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.reboot_error_message)
                    NOS_API.set_error_message("Reboot")
                    error_codes = NOS_API.test_cases_results_info.reboot_error_code
                    error_messages = NOS_API.test_cases_results_info.reboot_error_message
                    test_result = "FAIL"
                    NOS_API.deinitialize()
                    NOS_API.add_test_case_result_to_file_report(
                            test_result,
                            "- - - - - - - - - - - - - - - - - - - -",
                            "- - - - - - - - - - - - - - - - - - - -",
                            error_codes,
                            error_messages)
                
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                NOS_API.test_cases_results_info.nos_sap_number,
                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                NOS_API.test_cases_results_info.mac_using_barcode,
                                end_time)
                    NOS_API.upload_file_report(report_file)
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                        
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)

                    return
                    
                ## Record video with duration of recording (10 seconds)
                NOS_API.record_video("HD_Video", MAX_RECORD_VIDEO_TIME)
        
                ## Instance of PQMAnalyse type
                pqm_analyse = TEST_CREATION_API.PQMAnalyse()
        
                ## Set what algorithms should be checked while analyzing given video file with PQM.
                # Attributes are set to false by default.
                pqm_analyse.black_screen_activ = True
                pqm_analyse.blocking_activ = True
                pqm_analyse.freezing_activ = True
        
                # Name of the video file that will be analysed by PQM.
                pqm_analyse.file_name = "HD_Video"
        
                ## Analyse recorded video
                analysed_video = TEST_CREATION_API.pqm_analysis(pqm_analyse)
        
                if (pqm_analyse.black_screen_detected == TEST_CREATION_API.AlgorythmResult.DETECTED):
                    pqm_analyse_check = False
                    TEST_CREATION_API.write_log_to_file("Black Screen detected on recorded Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_1080p_image_absence_error_code \
                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_1080p_image_absence_error_message)
                            
                    error_codes = NOS_API.test_cases_results_info.hdmi_1080p_image_absence_error_code
                    error_messages = NOS_API.test_cases_results_info.hdmi_1080p_image_absence_error_message
        
                if (pqm_analyse.blocking_detected == TEST_CREATION_API.AlgorythmResult.DETECTED):
                    pqm_analyse_check = False
                    TEST_CREATION_API.write_log_to_file("Blocking detected on recorded Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_1080p_blocking_error_code \
                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_1080p_blocking_error_message)
                            
                    if (error_codes == ""):
                        error_codes = NOS_API.test_cases_results_info.hdmi_1080p_blocking_error_code
                    else:
                        error_codes = error_codes + " " + NOS_API.test_cases_results_info.hdmi_1080p_blocking_error_code
                    
                    if (error_messages == ""):
                        error_messages = NOS_API.test_cases_results_info.hdmi_1080p_blocking_error_message
                    else:
                        error_messages = error_messages + " " + NOS_API.test_cases_results_info.hdmi_1080p_blocking_error_message
                
                if (pqm_analyse.freezing_detected == TEST_CREATION_API.AlgorythmResult.DETECTED):
                    pqm_analyse_check = False
                    TEST_CREATION_API.write_log_to_file("Freezing detected on recorded Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_code \
                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_message)
                            
                    if (error_codes == ""):
                        error_codes = NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_code
                    else:
                        error_codes = error_codes + " " + NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_code
                        
                    if (error_messages == ""):
                        error_messages = NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_message
                    else:
                        error_messages = error_messages + " " + NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_message
                
                if not(pqm_analyse_check):  
                    NOS_API.set_error_message("Video HDMI")
                    NOS_API.add_test_case_result_to_file_report(
                            test_result,
                            "- - - - - - - - - - - - - - - - - - - -",
                            "- - - - - - - - - - - - - - - - - - - -",
                            error_codes,
                            error_messages)
                
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                NOS_API.test_cases_results_info.nos_sap_number,
                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                NOS_API.test_cases_results_info.mac_using_barcode,
                                end_time)
                    NOS_API.upload_file_report(report_file)
                    NOS_API.test_cases_results_info.isTestOK = False
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                        
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                    
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()                    
                    return
                
                if not(analysed_video):
                    TEST_CREATION_API.write_log_to_file("Could'n't Record Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.grabber_error_code \
                                                                        + "; Error message: " + NOS_API.test_cases_results_info.grabber_error_message)
                    error_codes = NOS_API.test_cases_results_info.grabber_error_code
                    error_messages = NOS_API.test_cases_results_info.grabber_error_message
                    NOS_API.set_error_message("Inspection")
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                    NOS_API.test_cases_results_info.nos_sap_number,
                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                    end_time)
                    NOS_API.upload_file_report(report_file)
                    NOS_API.test_cases_results_info.isTestOK = False
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                            test_result,
                            end_time,
                            error_codes,
                            report_file)
            
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return            
                
                ## Check if video is playing (check if video is not freezed)
                if (NOS_API.is_video_playing(TEST_CREATION_API.VideoInterface.HDMI1, NOS_API.ResolutionType.resolution_1080p, False)):     
                    if not(NOS_API.grab_picture("HD_Video_Channel")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    
                    Video_Result = NOS_API.compare_pictures("HDMI_HD_Video_1080_ref", "HD_Video_Channel", "[HALF_SCREEN_HD]") 
                    Video_Result_1 = NOS_API.compare_pictures("HDMI_HD_Video_1080_Voltar_ref", "HD_Video_Channel", "[HALF_SCREEN_HD]")
                    ## Record Audio from HDMI
                    TEST_CREATION_API.record_audio("HD_Audio_Channel", MAX_RECORD_AUDIO_TIME)

                    Audio_Result = NOS_API.compare_audio("No_Both_ref", "HD_Audio_Channel")
                    if(Audio_Result >= TEST_CREATION_API.AUDIO_THRESHOLD):
                        NOS_API.display_custom_dialog("Confirme o cabo HDMI", 1, ["Continuar"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG)
                        time.sleep(1)                       
                        ## Record Audio from HDMI
                        TEST_CREATION_API.record_audio("HD_Audio_Channel_1", MAX_RECORD_AUDIO_TIME)
                        Audio_Result = NOS_API.compare_audio("No_Both_ref", "HD_Audio_Channel_1")
                        
                        if(Audio_Result >= TEST_CREATION_API.AUDIO_THRESHOLD):
                            try:
                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                            except: 
                                pass
                                
                            NOS_API.Inspection = True
                            
                            if (NOS_API.configure_power_switch_by_inspection()):
                                if not(NOS_API.power_off()): 
                                    TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                                    ## Update test result
                                    TEST_CREATION_API.update_test_result(test_result)
                                    NOS_API.set_error_message("Inspection")
                                    
                                    NOS_API.add_test_case_result_to_file_report(
                                                    test_result,
                                                    "- - - - - - - - - - - - - - - - - - - -",
                                                    "- - - - - - - - - - - - - - - - - - - -",
                                                    error_codes,
                                                    error_messages)
                                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                                    report_file = ""
                                    if (test_result != "PASS"):
                                        report_file = NOS_API.create_test_case_log_file(
                                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                                        NOS_API.test_cases_results_info.nos_sap_number,
                                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                        "",
                                                        end_time)
                                        NOS_API.upload_file_report(report_file)
                                        NOS_API.test_cases_results_info.isTestOK = False
                                    
                                    
                                    ## Update test result
                                    TEST_CREATION_API.update_test_result(test_result)
                                
                                    ## Return DUT to initial state and de-initialize grabber device
                                    NOS_API.deinitialize()
                                    
                                    NOS_API.send_report_over_mqtt_test_plan(
                                                test_result,
                                                end_time,
                                                error_codes,
                                                report_file)

                                    return
                                time.sleep(10)
                                ## Power on STB with energenie
                                if not(NOS_API.power_on()):
                                    TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                                    ## Update test result
                                    TEST_CREATION_API.update_test_result(test_result)
                                    NOS_API.set_error_message("Inspection")
                                    
                                    NOS_API.add_test_case_result_to_file_report(
                                                    test_result,
                                                    "- - - - - - - - - - - - - - - - - - - -",
                                                    "- - - - - - - - - - - - - - - - - - - -",
                                                    error_codes,
                                                    error_messages)
                                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                                    report_file = ""
                                    if (test_result != "PASS"):
                                        report_file = NOS_API.create_test_case_log_file(
                                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                                        NOS_API.test_cases_results_info.nos_sap_number,
                                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                        "",
                                                        end_time)
                                        NOS_API.upload_file_report(report_file)
                                        NOS_API.test_cases_results_info.isTestOK = False
                                    
                                    test_result = "FAIL"
                                    
                                    ## Update test result
                                    TEST_CREATION_API.update_test_result(test_result)
                                
                                    ## Return DUT to initial state and de-initialize grabber device
                                    NOS_API.deinitialize()
                                    
                                    NOS_API.send_report_over_mqtt_test_plan(
                                            test_result,
                                            end_time,
                                            error_codes,
                                            report_file)
                                    
                                    return
                                time.sleep(15)
                            else:
                                TEST_CREATION_API.write_log_to_file("Incorrect test place name")
                                
                                NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                                                + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                                NOS_API.set_error_message("Inspection")
                                
                                NOS_API.add_test_case_result_to_file_report(
                                                test_result,
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                "- - - - - - - - - - - - - - - - - - - -",
                                                error_codes,
                                                error_messages)
                                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
                                report_file = ""
                                if (test_result != "PASS"):
                                    report_file = NOS_API.create_test_case_log_file(
                                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                                    NOS_API.test_cases_results_info.nos_sap_number,
                                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                                    "",
                                                    end_time)
                                    NOS_API.upload_file_report(report_file)
                                    NOS_API.test_cases_results_info.isTestOK = False
                                
                                test_result = "FAIL"
                                ## Update test result
                                TEST_CREATION_API.update_test_result(test_result)
                                
                            
                                ## Return DUT to initial state and de-initialize grabber device
                                NOS_API.deinitialize()
                                
                                NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                                
                                return
                            
                            NOS_API.Inspection = False
                            
                            NOS_API.initialize_grabber()
                            
                            ## Start grabber device with HDMI on default video/audio source
                            NOS_API.grabber_start_video_source(TEST_CREATION_API.VideoInterface.HDMI1)
                            TEST_CREATION_API.grabber_start_audio_source(TEST_CREATION_API.AudioInterface.HDMI1)
                            time.sleep(3)
                                                        
                            ## Record audio from HDMI
                            TEST_CREATION_API.record_audio("HD_Audio_Channel_2", MAX_RECORD_AUDIO_TIME)
                            Audio_Result = NOS_API.compare_audio("No_Both_ref", "HD_Audio_Channel_2")
                        
                    if ((Video_Result >= TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD or Video_Result_1 >= TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD) and Audio_Result < TEST_CREATION_API.AUDIO_THRESHOLD):
                        HDMI_HD_1080_Test = True
                        NOS_API.send_command_uma_uma("back,back")                       
                    else: 
                        if (Video_Result >= TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD):
                            TEST_CREATION_API.write_log_to_file("Audio Absence on HDMI 1080p")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.hdmi_1080p_signal_absence_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_1080p_signal_absence_error_message)
                            NOS_API.set_error_message("Audio HDMI")
                            error_codes = NOS_API.test_cases_results_info.hdmi_1080p_signal_absence_error_code
                            error_messages = NOS_API.test_cases_results_info.hdmi_1080p_signal_absence_error_message
                        elif (Audio_Result < TEST_CREATION_API.AUDIO_THRESHOLD):
                            TEST_CREATION_API.write_log_to_file("Image Interferences on HDMI 1080p")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.hdmi_1080p_noise_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_1080p_noise_error_message)
                            NOS_API.set_error_message("Video HDMI")
                            error_codes = NOS_API.test_cases_results_info.hdmi_1080p_noise_error_code
                            error_messages = NOS_API.test_cases_results_info.hdmi_1080p_noise_error_message
                        else:
                            TEST_CREATION_API.write_log_to_file("Audio Absence and Image Interferences on HD Channel")
                            NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.hd_channel_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.hd_channel_error_message)
                            NOS_API.set_error_message("Tuner")
                            error_codes = NOS_API.test_cases_results_info.hd_channel_error_code
                            error_messages = NOS_API.test_cases_results_info.hd_channel_error_message
                else:
                    TEST_CREATION_API.write_log_to_file("Channel with TRC video was not playing on HDMI 1080p.")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_message)
                    error_codes = NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_code
                    error_messages = NOS_API.test_cases_results_info.hdmi_1080p_image_freezing_error_message
                    NOS_API.set_error_message("Video HDMI")
            
            ###############################################################################################################################################
            ################################################################ HDMI SD 720 Test #############################################################
            ###############################################################################################################################################
            if (HDMI_HD_1080_Test):
                ## Initialize PQM Test variable as True
                pqm_analyse_check = True 
                
                NOS_API.send_command_uma_uma("down,down,ok")  
                if not(NOS_API.grab_picture("HDMI_Menu")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("HDMI_Menu_ref", "HDMI_Menu", "[HDMI]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up,up,up,up,up,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,down,down,down,down,down,down,ok")
                    if not(NOS_API.grab_picture("HDMI_MenuScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("HDMI_Menu_ref", "HDMI_MenuScn", "[HDMI]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                NOS_API.send_command_uma_uma("left") 
                time.sleep(2)
                NOS_API.send_command_uma_uma("left") 
                time.sleep(2)
                NOS_API.send_command_uma_uma("back") 
                
                video_height = NOS_API.get_av_format_info(TEST_CREATION_API.AudioVideoInfoType.video_height)
                if (video_height != "720"):
                    NOS_API.set_error_message("Resolução")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.resolution_error_code \
                                                    + "; Error message: " + NOS_API.test_cases_results_info.resolution_error_message) 
                    error_codes = NOS_API.test_cases_results_info.resolution_error_code
                    error_messages = NOS_API.test_cases_results_info.resolution_error_message                     
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                
                NOS_API.send_command_uma_uma("up,up,ok")
                if not(NOS_API.grab_picture("Sintonization_720")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Sintonization_Menu_720_ref", "Sintonization_720", "[Sintonization_720]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up,up,up,up,up,up,up,up,up")
                    NOS_API.send_command_uma_uma("down,down,down,down,down,down,down,ok")
                    if not(NOS_API.grab_picture("Sintonization_720Scn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Sintonization_Menu_720_ref", "Sintonization_720Scn", "[Sintonization_720]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - " + str(tx_value) + " " + str(rx_value) + " " + str(downloadstream_snr_value) + " - - - - - " + str(cas_id_number) + " " + str(sw_version) + " - " + str(sc_number) + " - - - -",
                                    "- - - - <52 >-10<10 >=34 - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                NOS_API.send_command_uma_uma("down,down,down,down,5,1,3,6,ok,down,down,5,1,3,7,ok,down,down,5,1,3,6,ok,play")
                
                if not (NOS_API.is_signal_present_on_video_source()):
                    TEST_CREATION_API.write_log_to_file("STB lost Signal.Possible Reboot.")
                    
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.reboot_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.reboot_error_message)
                    NOS_API.set_error_message("Reboot")
                    error_codes = NOS_API.test_cases_results_info.reboot_error_code
                    error_messages = NOS_API.test_cases_results_info.reboot_error_message
                    test_result = "FAIL"
                    NOS_API.deinitialize()
                    NOS_API.add_test_case_result_to_file_report(
                            test_result,
                            "- - - - - - - - - - - - - - - - - - - -",
                            "- - - - - - - - - - - - - - - - - - - -",
                            error_codes,
                            error_messages)
                
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                NOS_API.test_cases_results_info.nos_sap_number,
                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                NOS_API.test_cases_results_info.mac_using_barcode,
                                end_time)
                    NOS_API.upload_file_report(report_file)
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                        
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)

                    return
                    
                ## Record video with duration of recording (10 seconds)
                NOS_API.record_video("SD_Video", MAX_RECORD_VIDEO_TIME)
        
                ## Instance of PQMAnalyse type
                pqm_analyse = TEST_CREATION_API.PQMAnalyse()
        
                ## Set what algorithms should be checked while analyzing given video file with PQM.
                # Attributes are set to false by default.
                pqm_analyse.black_screen_activ = True
                pqm_analyse.blocking_activ = True
                pqm_analyse.freezing_activ = True
        
                # Name of the video file that will be analysed by PQM.
                pqm_analyse.file_name = "SD_Video"
        
                ## Analyse recorded video
                analysed_video = TEST_CREATION_API.pqm_analysis(pqm_analyse)
        
                if (pqm_analyse.black_screen_detected == TEST_CREATION_API.AlgorythmResult.DETECTED):
                    pqm_analyse_check = False
                    TEST_CREATION_API.write_log_to_file("Black Screen detected on recorded Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_720p_image_absence_error_code \
                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_720p_image_absence_error_message)
                            
                    error_codes = NOS_API.test_cases_results_info.hdmi_720p_image_absence_error_code
                    error_messages = NOS_API.test_cases_results_info.hdmi_720p_image_absence_error_message
        
                if (pqm_analyse.blocking_detected == TEST_CREATION_API.AlgorythmResult.DETECTED):
                    pqm_analyse_check = False
                    TEST_CREATION_API.write_log_to_file("Blocking detected on recorded Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_720p_blocking_error_code \
                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_720p_blocking_error_message)
                            
                    if (error_codes == ""):
                        error_codes = NOS_API.test_cases_results_info.hdmi_720p_blocking_error_code
                    else:
                        error_codes = error_codes + " " + NOS_API.test_cases_results_info.hdmi_720p_blocking_error_code
                    
                    if (error_messages == ""):
                        error_messages = NOS_API.test_cases_results_info.hdmi_720p_blocking_error_message
                    else:
                        error_messages = error_messages + " " + NOS_API.test_cases_results_info.hdmi_720p_blocking_error_message
                
                if (pqm_analyse.freezing_detected == TEST_CREATION_API.AlgorythmResult.DETECTED):
                    pqm_analyse_check = False
                    TEST_CREATION_API.write_log_to_file("Freezing detected on recorded Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_code \
                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_message)
                            
                    if (error_codes == ""):
                        error_codes = NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_code
                    else:
                        error_codes = error_codes + " " + NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_code
                        
                    if (error_messages == ""):
                        error_messages = NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_message
                    else:
                        error_messages = error_messages + " " + NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_message
                
                if not(pqm_analyse_check):  
                    NOS_API.set_error_message("Video HDMI")
                    NOS_API.add_test_case_result_to_file_report(
                            test_result,
                            "- - - - - - - - - - - - - - - - - - - -",
                            "- - - - - - - - - - - - - - - - - - - -",
                            error_codes,
                            error_messages)
                
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                NOS_API.test_cases_results_info.s_n_using_barcode,
                                NOS_API.test_cases_results_info.nos_sap_number,
                                NOS_API.test_cases_results_info.cas_id_using_barcode,
                                NOS_API.test_cases_results_info.mac_using_barcode,
                                end_time)
                    NOS_API.upload_file_report(report_file)
                    NOS_API.test_cases_results_info.isTestOK = False
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                    
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                    
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                
                if not(analysed_video):
                    TEST_CREATION_API.write_log_to_file("Could'n't Record Video")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.grabber_error_code \
                                                                        + "; Error message: " + NOS_API.test_cases_results_info.grabber_error_message)
                    error_codes = NOS_API.test_cases_results_info.grabber_error_code
                    error_messages = NOS_API.test_cases_results_info.grabber_error_message
                    NOS_API.set_error_message("Inspection")
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = NOS_API.create_test_case_log_file(
                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                    NOS_API.test_cases_results_info.nos_sap_number,
                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                    end_time)
                    NOS_API.upload_file_report(report_file)
                    NOS_API.test_cases_results_info.isTestOK = False
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                            test_result,
                            end_time,
                            error_codes,
                            report_file)
            
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return            
                
                ## Check if video is playing (check if video is not freezed)
                if (NOS_API.is_video_playing()):
                    if not(NOS_API.grab_picture("SD_Video_Channel")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    
                    Video_Result = NOS_API.compare_pictures("HDMI_SD_Video_720_ref", "SD_Video_Channel", "[HALF_SCREEN_SD]")
                    Video_Result_1 = NOS_API.compare_pictures("HDMI_SD_Video_720_Voltar_ref", "SD_Video_Channel", "[HALF_SCREEN_SD]")
                    
                    ## Record audio from digital output (HDMI)
                    TEST_CREATION_API.record_audio("SD_Audio_Channel", MAX_RECORD_AUDIO_TIME)
            
                    ## Compare recorded and expected audio and get result of comparison
                    Audio_Result = NOS_API.compare_audio("No_Both_ref", "SD_Audio_Channel")
                    if(Audio_Result >= TEST_CREATION_API.AUDIO_THRESHOLD):
                        NOS_API.display_custom_dialog("Confirme o cabo HDMI", 1, ["Continuar"], NOS_API.WAIT_TIME_TO_CLOSE_DIALOG)
                        time.sleep(1)
                        TEST_CREATION_API.record_audio("SD_Audio_Channel_1", MAX_RECORD_AUDIO_TIME)
                        Audio_Result = NOS_API.compare_audio("No_Both_ref", "SD_Audio_Channel_1")
            
                    if ((Video_Result >= TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD or Video_Result_1 >= TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD) and Audio_Result < TEST_CREATION_API.AUDIO_THRESHOLD):
                        HDMI_SD_720_Test = True
                        NOS_API.send_command_uma_uma("back,back") 
                    else:
                        if (Video_Result >= TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD):
                            TEST_CREATION_API.write_log_to_file("Audio Absence on HDMI 720p")
                            NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_720p_signal_absence_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.hdmi_720p_signal_absence_error_message)
                            error_codes = NOS_API.test_cases_results_info.hdmi_720p_signal_absence_error_code
                            error_messages = NOS_API.test_cases_results_info.hdmi_720p_signal_absence_error_message
                            NOS_API.set_error_message("Audio HDMI")
                        elif (Audio_Result < TEST_CREATION_API.AUDIO_THRESHOLD):
                            TEST_CREATION_API.write_log_to_file("Image Interferences on HDMI 720p")
                            NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_720p_noise_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.hdmi_720p_noise_error_message)
                            error_codes = NOS_API.test_cases_results_info.hdmi_720p_noise_error_code
                            error_messages = NOS_API.test_cases_results_info.hdmi_720p_noise_error_message
                            NOS_API.set_error_message("Video HDMI") 
                        else:
                            TEST_CREATION_API.write_log_to_file("Audio Absence and Image Interferences on HD Channel")
                            NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.sd_channel_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.sd_channel_error_message)
                            error_codes = NOS_API.test_cases_results_info.sd_channel_error_code
                            error_messages = NOS_API.test_cases_results_info.sd_channel_error_message
                            NOS_API.set_error_message("Tuner") 
                else:
                    TEST_CREATION_API.write_log_to_file("Channel with TRC video was not playing on HDMI 720p.")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_message)
                    error_codes = NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_code
                    error_messages = NOS_API.test_cases_results_info.hdmi_720p_image_freezing_error_message
                    NOS_API.set_error_message("Video HDMI")
           
            ###############################################################################################################################################
            ################################################################ HDMI 4K 2160 Test ############################################################
            ###############################################################################################################################################
            if (HDMI_SD_720_Test):
                HDMI_4k_2160_Test = True
            
            ###############################################################################################################################################
            ################################################################ Factory Reset Test ###########################################################
            ###############################################################################################################################################
            if (HDMI_4k_2160_Test):
                NOS_API.send_command_uma_uma("up,up,up,up,up,up,up,up,ok")
                if not(NOS_API.grab_picture("Factory_Reset")):
                    TEST_CREATION_API.write_log_to_file("HDMI NOK")
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                            + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                    NOS_API.set_error_message("Video HDMI")
                    error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                    error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    report_file = ""    
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file) 
                        NOS_API.test_cases_results_info.isTestOK = False
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    return
                if not(TEST_CREATION_API.compare_pictures("Factory_Reset_Menu_ref", "Factory_Reset", "[FactoryReset]")):
                    NOS_API.send_command_uma_uma("back,back,back,ok,up,up,up,up,up,up,up,up,up,up,up,up,ok")
                    if not(NOS_API.grab_picture("Factory_ResetScn")):
                        TEST_CREATION_API.write_log_to_file("HDMI NOK")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.image_absence_hdmi_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.image_absence_hdmi_error_message)
                        NOS_API.set_error_message("Video HDMI")
                        error_codes = NOS_API.test_cases_results_info.image_absence_hdmi_error_code
                        error_messages = NOS_API.test_cases_results_info.image_absence_hdmi_error_message
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            NOS_API.test_cases_results_info.mac_using_barcode,
                                            end_time)
                            NOS_API.upload_file_report(report_file) 
                            NOS_API.test_cases_results_info.isTestOK = False
                            
                            NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                    
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                    if not(TEST_CREATION_API.compare_pictures("Factory_Reset_Menu_ref", "Factory_ResetScn", "[FactoryReset]")):
                        TEST_CREATION_API.write_log_to_file("Didn't Navigate to Product Information Menu")    
                        NOS_API.set_error_message("Navegação")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.navigation_error_code \
                                                                + "; Error message: " + NOS_API.test_cases_results_info.navigation_error_message) 
                        error_codes = NOS_API.test_cases_results_info.navigation_error_code
                        error_messages = NOS_API.test_cases_results_info.navigation_error_message                    
                        
                        NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                        
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = ""    
                        
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        NOS_API.test_cases_results_info.mac_using_barcode,
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)

                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)

                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        return
                
                NOS_API.send_command_uma_uma("ok")
                
                Factory_Reset_Result = NOS_API.wait_for_multiple_pictures(["Factory_Reset_Result_ref"], 10, ["[FactoryReset_Result]"], [TEST_CREATION_API.DEFAULT_HDMI_VIDEO_THRESHOLD])
                
                if Factory_Reset_Result != -1 and Factory_Reset_Result != -2:
                    test_result = "PASS"

                    NOS_API.configure_power_switch_by_inspection()
                    if not(NOS_API.power_off()):
                        TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                        
                        NOS_API.set_error_message("POWER SWITCH")
                        NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                            + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                        error_codes = NOS_API.test_cases_results_info.power_switch_error_code
                        error_messages = NOS_API.test_cases_results_info.power_switch_error_message
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        NOS_API.add_test_case_result_to_file_report(
                                test_result,
                                "- - - - - - - - - - - - - - - - - - - -",
                                "- - - - - - - - - - - - - - - - - - - -",
                                error_codes,
                                error_messages)
                    
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        report_file = NOS_API.create_test_case_log_file(
                                    NOS_API.test_cases_results_info.s_n_using_barcode,
                                    NOS_API.test_cases_results_info.nos_sap_number,
                                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                                    NOS_API.test_cases_results_info.mac_using_barcode,
                                    end_time)
                        NOS_API.upload_file_report(report_file)
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                            test_result,
                            end_time,
                            error_codes,
                            report_file)
                        
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                        
                        return
                else:
                    TEST_CREATION_API.write_log_to_file("Factory Reset Fail")
                    NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.measure_boot_time_error_code \
                                                + "; Error message: " + NOS_API.test_cases_results_info.measure_boot_time_error_message)
                    NOS_API.set_error_message("Factory Reset")  
                    error_codes = NOS_API.test_cases_results_info.measure_boot_time_error_code
                    error_messages = NOS_API.test_cases_results_info.measure_boot_time_error_message
                
            System_Failure = 2
        except Exception as error:
            if(System_Failure == 0):
                System_Failure = System_Failure + 1 
                NOS_API.Inspection = True
                if(System_Failure == 1):
                    try:
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        TEST_CREATION_API.write_log_to_file(str(error))
                    except: 
                        pass

                if (NOS_API.configure_power_switch_by_inspection()):
                    if not(NOS_API.power_off()): 
                        TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                        NOS_API.set_error_message("Inspection")
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                        report_file = ""
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            "",
                                            end_time)
                            NOS_API.upload_file_report(report_file)
                            NOS_API.test_cases_results_info.isTestOK = False
                        
                        
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                    test_result,
                                    end_time,
                                    error_codes,
                                    report_file)
                
                        return
                    time.sleep(10)
                    ## Power on STB with energenie
                    if not(NOS_API.power_on()):
                        TEST_CREATION_API.write_log_to_file("Comunication with PowerSwitch Fails")
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                        NOS_API.set_error_message("Inspection")
                        
                        NOS_API.add_test_case_result_to_file_report(
                                        test_result,
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        "- - - - - - - - - - - - - - - - - - - -",
                                        error_codes,
                                        error_messages)
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                        report_file = ""
                        if (test_result != "PASS"):
                            report_file = NOS_API.create_test_case_log_file(
                                            NOS_API.test_cases_results_info.s_n_using_barcode,
                                            NOS_API.test_cases_results_info.nos_sap_number,
                                            NOS_API.test_cases_results_info.cas_id_using_barcode,
                                            "",
                                            end_time)
                            NOS_API.upload_file_report(report_file)
                            NOS_API.test_cases_results_info.isTestOK = False
                        
                        test_result = "FAIL"
                        
                        ## Update test result
                        TEST_CREATION_API.update_test_result(test_result)
                    
                        ## Return DUT to initial state and de-initialize grabber device
                        NOS_API.deinitialize()
                        
                        NOS_API.send_report_over_mqtt_test_plan(
                                test_result,
                                end_time,
                                error_codes,
                                report_file)
                        
                        return
                    time.sleep(10)
                else:
                    TEST_CREATION_API.write_log_to_file("Incorrect test place name")
                    
                    NOS_API.update_test_slot_comment("Error code = " + NOS_API.test_cases_results_info.power_switch_error_code \
                                                                    + "; Error message: " + NOS_API.test_cases_results_info.power_switch_error_message)
                    NOS_API.set_error_message("Inspection")
                    
                    NOS_API.add_test_case_result_to_file_report(
                                    test_result,
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    "- - - - - - - - - - - - - - - - - - - -",
                                    error_codes,
                                    error_messages)
                    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
                    report_file = ""
                    if (test_result != "PASS"):
                        report_file = NOS_API.create_test_case_log_file(
                                        NOS_API.test_cases_results_info.s_n_using_barcode,
                                        NOS_API.test_cases_results_info.nos_sap_number,
                                        NOS_API.test_cases_results_info.cas_id_using_barcode,
                                        "",
                                        end_time)
                        NOS_API.upload_file_report(report_file)
                        NOS_API.test_cases_results_info.isTestOK = False
                    
                    test_result = "FAIL"
                    ## Update test result
                    TEST_CREATION_API.update_test_result(test_result)
                    
                
                    ## Return DUT to initial state and de-initialize grabber device
                    NOS_API.deinitialize()
                    
                    NOS_API.send_report_over_mqtt_test_plan(
                        test_result,
                        end_time,
                        error_codes,
                        report_file)
                    
                    return
                
                NOS_API.Inspection = False
            else:
                test_result = "FAIL"
                TEST_CREATION_API.write_log_to_file(error)
                NOS_API.update_test_slot_comment("Error code: " + NOS_API.test_cases_results_info.grabber_error_code \
                                                                    + "; Error message: " + NOS_API.test_cases_results_info.grabber_error_message)
                error_codes = NOS_API.test_cases_results_info.grabber_error_code
                error_messages = NOS_API.test_cases_results_info.grabber_error_message
                NOS_API.set_error_message("Inspection")
                System_Failure = 2   

    NOS_API.add_test_case_result_to_file_report(
                    test_result,
                    "- - - - - - - - - - - - - - - - - - - -",
                    "- - - - - - - - - - - - - - - - - - - -",
                    error_codes,
                    error_messages)
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   
    report_file = ""    

    report_file = NOS_API.create_test_case_log_file(
                    NOS_API.test_cases_results_info.s_n_using_barcode,
                    NOS_API.test_cases_results_info.nos_sap_number,
                    NOS_API.test_cases_results_info.cas_id_using_barcode,
                    NOS_API.test_cases_results_info.mac_using_barcode,
                    end_time)
    NOS_API.upload_file_report(report_file) 
    NOS_API.test_cases_results_info.isTestOK = False
    
    NOS_API.send_report_over_mqtt_test_plan(
            test_result,
            end_time,
            error_codes,
            report_file)

    ## Update test result
    TEST_CREATION_API.update_test_result(test_result)
    
    ## Return DUT to initial state and de-initialize grabber device
    NOS_API.deinitialize()