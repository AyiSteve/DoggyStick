/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronåics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"
#include "tim.h"
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include "usart.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
typedef struct {
    int dir;
    int seconds;
} MotorCommand_t;
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */

/* USER CODE END Variables */
osThreadId_t Task_MotorHandle;
const osThreadAttr_t Task_Motor_attributes = {
  .name = "Task_Motor",
  .stack_size = 128*10,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for Task_Ultrasonic */
osThreadId_t Task_UltrasonicHandle;
const osThreadAttr_t Task_Ultrasonic_attributes = {
  .name = "Task_Ultrasonic",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};

/* Definitions for Task_Display */
osThreadId_t Task_DisplayHandle;
const osThreadAttr_t Task_Display_attributes = {
  .name = "Task_Display",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for Task_Bluetooth */
osThreadId_t Task_BluetoothHandle;
const osThreadAttr_t Task_Bluetooth_attributes = {
  .name = "Task_Bluetooth",
  .stack_size = 4096,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for distanceQueue */
osMessageQueueId_t distanceQueueHandle;
const osMessageQueueAttr_t distanceQueue_attributes = {
  .name = "distanceQueue"
};
/* Definitions for myMutex01 */
osMutexId_t myMutex01Handle;
const osMutexAttr_t myMutex01_attributes = {
  .name = "myMutex01"
};
/* Definitions for myBinarySem01 */
osSemaphoreId_t myBinarySem01Handle;
const osSemaphoreAttr_t myBinarySem01_attributes = {
  .name = "myBinarySem01"
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* MOTOR CONTROL FUNCTIONS */

static void left_forward(uint16_t pwm)
{
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_12, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_13, GPIO_PIN_RESET);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, pwm);
}

static void right_forward(uint16_t pwm)
{
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_14, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_15, GPIO_PIN_RESET);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, pwm);
}

static void left_backward(uint16_t pwm)
{
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_12, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_13, GPIO_PIN_SET);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, pwm);
}

static void right_backward(uint16_t pwm)
{
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_14, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_15, GPIO_PIN_SET);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, pwm);
}

static void stop_all(void)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, 0);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, 0);
}

static void turn_right(uint16_t speed)
{
    left_forward(speed);
    right_backward(speed);
}

static void turn_left(uint16_t speed)
{
    left_backward(speed);
    right_forward(speed);
}

static void go_straight(uint16_t speed)
{
    left_forward(speed);
    right_forward(speed);
}
void Task_Motor(void *argument)
{
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_6, GPIO_PIN_SET); // enable motor driver

    MotorCommand_t cmd;
    int active_dir = 4;  // 4 = stop
    uint32_t end_tick = 0;
    const uint16_t speed = 40000;

    stop_all();

    for(;;)
    {
        // Check if a new command arrived, but do NOT block forever
        if (osMessageQueueGet(distanceQueueHandle, &cmd, NULL, 0) == osOK)
        {
            active_dir = cmd.dir;
            end_tick = HAL_GetTick() + (uint32_t)(cmd.seconds * 1000);
        }

        // Execute current state
        switch(active_dir)
        {
            case 1: // left
                turn_left(speed);
                break;

            case 2: // right
                turn_right(speed);
                break;

            case 3: // straight
                go_straight(speed);
                break;

            case 4: // stop
            default:
                stop_all();
                break;
        }

        // Auto-stop when time expires
        if (active_dir != 4 && HAL_GetTick() >= end_tick)
        {
            active_dir = 4;
            stop_all();
        }

        HAL_GPIO_TogglePin(LD4_GPIO_Port, LD4_Pin); // debug heartbeat
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

void Task_Ultrasonic(void *argument)
{
    for(;;)
    {
      	HCSR04_Update();
         osDelay(50);

    }
}

void Task_Display(void *argument)
{
    char lcd_buf0[16];
    char lcd_buf1[16];

    for(;;)
    {
        float d0 = HCSR04_GetDistance(0);
        float d1 = HCSR04_GetDistance(1);
        float d2 = HCSR04_GetDistance(2);

        snprintf(lcd_buf0, sizeof(lcd_buf0), "Dist: %.2f", d0);
        snprintf(lcd_buf1, sizeof(lcd_buf1), "%.2f  %.2f", d1, d2);

        HD44780_SetCursor(0,0);
        HD44780_PrintStr(lcd_buf0);
        HD44780_SetCursor(0,1);
        HD44780_PrintStr(lcd_buf1);

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}



void Task_Bluetooth(void *argument)
{
    char msg[64];
    char rx_buffer[32];
    uint8_t ch;
    int idx = 0;
    MotorCommand_t cmd;

    for(;;)
    {
        // --- receive one command line: "dir,seconds\n"
        idx = 0;
        memset(rx_buffer, 0, sizeof(rx_buffer));

        while (idx < (int)(sizeof(rx_buffer) - 1))
        {
            if (HAL_UART_Receive(&huart3, &ch, 1, 50) == HAL_OK)
            {
                if (ch == '\n' || ch == '\r')
                    break;

                rx_buffer[idx++] = ch;
            }
            else
            {
                vTaskDelay(pdMS_TO_TICKS(5));
                continue;
            }
        }

        // parse command if something arrived
        if (idx > 0)
        {
            cmd.dir = 0;
            cmd.seconds = 0;

            if (sscanf(rx_buffer, "%d,%d", &cmd.dir, &cmd.seconds) == 2)
            {
                osMessageQueuePut(distanceQueueHandle, &cmd, 0, 0);
            }
        }

        // --- send telemetry
        float d0 = HCSR04_GetDistance(0);
        float d1 = HCSR04_GetDistance(1);
        float d2 = HCSR04_GetDistance(2);

        snprintf(msg, sizeof(msg), "%.2f,%.2f,%.2f\r\n", d0, d1, d2);
        HAL_UART_Transmit(&huart3, (uint8_t*)msg, strlen(msg), 100);

            vTaskDelay(pdMS_TO_TICKS(200));

    }
}
/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void *argument);
void StartTask03(void *argument);
void StartTask04(void *argument);

extern void MX_USB_HOST_Init(void);
void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */
  /* Create the mutex(es) */
  /* creation of myMutex01 */
  myMutex01Handle = osMutexNew(&myMutex01_attributes);

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* Create the semaphores(s) */
  /* creation of myBinarySem01 */
  myBinarySem01Handle = osSemaphoreNew(1, 1, &myBinarySem01_attributes);

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* creation of distanceQueue */
  distanceQueueHandle = osMessageQueueNew (16, sizeof(MotorCommand_t), &distanceQueue_attributes);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of Task_Ultrasonic */
  Task_UltrasonicHandle = osThreadNew(Task_Ultrasonic, NULL, &Task_Ultrasonic_attributes);
  /* creation of Task_Motor */
  Task_MotorHandle = osThreadNew(Task_Motor, NULL, &Task_Motor_attributes);
  /* creation of Task_Display */
  // Task_DisplayHandle = osThreadNew(StartTask03, NULL, &Task_Display_attributes);

  /* creation of Task_Bluetooth */
  Task_BluetoothHandle = osThreadNew(Task_Bluetooth, NULL, &Task_Bluetooth_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* init code for USB_HOST */
  MX_USB_HOST_Init();
  /* USER CODE BEGIN StartDefaultTask */
  /* Infinite loop */
  for(;;)
  {


    osDelay(200);
  }
  /* USER CODE END StartDefaultTask */
}

/* USER CODE BEGIN Header_StartTask03 */
/**
* @brief Function implementing the Task_Ultrasonic thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask03 */
void StartTask03(void *argument)
{
  /* USER CODE BEGIN StartTask03 */
  /* Infinite loop */
  for(;;)
  {
    osDelay(1);
  }
  /* USER CODE END StartTask03 */
}

/* USER CODE BEGIN Header_StartTask04 */
/**
* @brief Function implementing the Task_Bluetooth thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTask04 */
void StartTask04(void *argument)
{
  /* USER CODE BEGIN StartTask04 */
  /* Infinite loop */
  for(;;)
  {
    osDelay(1);
  }
  /* USER CODE END StartTask04 */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */

