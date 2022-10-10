library(dplyr)
library(ggplot2)


# Load data ---------------------------------------------------------------


results <- read.csv('/2_metaMIMIC_experiment_1/results.csv')
results_exp2 <- read.csv('/metaMIMIC/3_metaMIMIC_experiment_2/results.csv')
results_memento <- read.csv('/mementoML_results/results.csv')
results_bayes <-  read.csv('/6_metaMIMIC_experiment_bayes/results.csv')

grid_memento <- read.csv('/mementoML_results/grid.csv')

grid_param_saved <- read.csv('/2_metaMIMIC_experiment_1/grid.csv')
grid_param <- results %>% 
  select(set_index, booster, subsample, max_depth, min_child_weight,
         colsample_bytree, colsample_bylevel, n_estimators, learning_rate) %>% 
  unique()

head(results)

results_mimic_auc <- results %>% 
  group_by(set_index, target) %>% 
  summarise(AUC = mean(AUC))

results_exp2_mimic_auc <- results_exp2 %>% 
  group_by(set_index, target, half) %>% 
  summarise(AUC = mean(AUC))

results_agg <- results %>% 
  group_by(target) %>% 
  mutate(value_scaled = (AUC - min(AUC))/(max(AUC) - min(AUC))) %>% 
  group_by(set_index, target) %>% 
  summarise(value = mean(value_scaled))

results_agg_exp2 <- results_exp2 %>% 
  group_by(target, half) %>% 
  mutate(value_scaled =  (AUC - min(AUC))/(max(AUC) - min(AUC))) %>% 
  group_by(set_index, target, half) %>% 
  summarise(value = mean(value_scaled))




CANE <- function(results_agg){
  
  portfolio_idx <- c()
  base_best_value <- 0
  repeat{
    # browser()
    if(length(portfolio_idx) == 0){
      ext_portfolio <- results_agg %>% 
        group_by(set_index) %>% 
        summarise(sum_value_max = sum(value))
      
      
    }else{
      portfolio_power <- results_agg %>% 
        ungroup() %>% 
        filter(set_index %in% portfolio_idx) %>% 
        tidyr::pivot_wider(id_cols = set_index, names_from = target, values_from = value) %>% 
        select(-set_index) %>% 
        summarise_all(max) %>% 
        tidyr::pivot_longer(cols= everything(), names_to = 'target', values_to = 'value_portfolio')
      
      
      
      ext_portfolio <- results_agg %>% 
        ungroup() %>% 
        filter(!set_index %in% portfolio_idx) %>% 
        left_join(portfolio_power) %>% 
        group_by(set_index, target) %>% 
        mutate(value_max = max(c(value, value_portfolio))) %>% 
        group_by(set_index) %>% 
        summarise(sum_value_max = sum(value_max)) 
    }
    
    
    ext_best_value <- max(ext_portfolio$sum_value_max)
    
    if(ext_best_value == base_best_value | nrow(ext_portfolio) == 0) break
    
    if(ext_best_value > base_best_value){
      
      base_best_value <- ext_best_value
      portfolio_idx <- c(portfolio_idx,
                         ext_portfolio$set_index[which.max(ext_portfolio$sum_value_max)[1]])
    }
    
    
  }
  return(list(portfolio = portfolio_idx, measure = base_best_value))
}

# CANE(results_agg[results_agg$set_index == 1,])
# CANE(results_agg)

A_SMFO <- function(results_agg){
  
  df <- results_agg
  portfolio_list <- list()
  while(nrow(df)>0){
    sel_set_index <- CANE(df)
    portfolio_list[[length(portfolio_list) + 1]] <- sel_set_index
    
    df <- df %>% 
      filter(!set_index %in% sel_set_index$portfolio)
    
    
    
  }
  
  portfolio_list
}

SIMPLE_RANK <- function(results_agg){
  
  x <- results_agg %>% 
    group_by(set_index) %>% 
    summarise(mean_rank = mean(value))
  x$set_index[order(-x$mean_rank)]
}


### Results for MIMIC- EXP 1 ----------------------
ranking_exc_dataset <- list()

for(target_sel in unique(results_agg$target)){
  # browser()
  
  
  results_agg_portfolio <- results_agg %>% 
    filter(!target %in% target_sel)
  
  portfolio_greedy <- A_SMFO(results_agg_portfolio)
  portfolio_simple <- SIMPLE_RANK(results_agg_portfolio)
  
  results_agg_sel <- results_agg %>% 
    filter(target %in% target_sel)
  
  sel_ranking_mM1_greedy <- results_agg_sel[unlist(sapply(portfolio_greedy, function(x) x[['portfolio']]))+1,]
  sel_ranking_mM1_simple <- results_agg_sel[portfolio_simple+1,]
  
  sel_ranking_mM1_greedy <- sel_ranking_mM1_greedy %>% 
    ungroup() %>% 
    mutate(cummax_value = cummax(value),
           ADTM = abs(cummax_value - max(value)))
  sel_ranking_mM1_simple <- sel_ranking_mM1_simple %>% 
    ungroup() %>% 
    mutate(cummax_value = cummax(value),
           ADTM = abs(cummax_value - max(value)))
  ranking_exc_dataset[[length(ranking_exc_dataset)+1]] <- list(target = target_sel,
                                                               portfolio_greedy = portfolio_greedy,
                                                               portfolio_simple = portfolio_simple,
                                                               ranking_greedy = sel_ranking_mM1_greedy,
                                                               ranking_simple = sel_ranking_mM1_simple)
  
}





for(i in seq_along(ranking_exc_dataset)){
  
  target_df_name <- ranking_exc_dataset[[i]]$target
  
  portfolio_greedy <- unlist(sapply(ranking_exc_dataset[[i]]$portfolio_greedy, function(x) x$portfolio ))
  portfolio_simple <- ranking_exc_dataset[[i]]$portfolio_simple
  
  portfolio_greedy <- data.frame(iter = 1:length(portfolio_greedy),
                                 param_index = portfolio_greedy)
  
  portfolio_simple <- data.frame(iter = 1:length(portfolio_simple),
                                 param_index = portfolio_simple)
  portfolio_greedy <-portfolio_greedy %>% 
    left_join(grid_param, by = c('param_index' = 'set_index')) %>% 
    mutate(param_index = param_index + 1002)
  portfolio_simple <-portfolio_simple %>% 
    left_join(grid_param, by = c('param_index' = 'set_index')) %>% 
    mutate(param_index = param_index + 1002)
  # browser()
  write.csv(portfolio_greedy,
            paste0('/portfolios/csv/portfolio_ASMFO_MIMIC_out_', i, '_', target_df_name, '.csv'),
            row.names = FALSE)
  write.csv(portfolio_simple, 
            paste0('/portfolios/csv/portfolio_AR_MIMIC_out_', i, '_', target_df_name, '.csv'),
            row.names = FALSE)
  
}
